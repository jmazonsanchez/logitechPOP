#!/usr/bin/env python3
"""
dictate.py - Módulo de Dictado por Voz Offline para Logitech POP Keys
Utiliza Whisper.cpp local y PipeWire para transcripción de voz a texto privada,
sin conexión a internet, con detección de silencio automática (VAD)
y auto-pegado instantáneo en la ventana activa de Wayland y X11.
"""

import os
import sys
import time
import math
import struct
import shutil
import signal
import subprocess
import re
import socket
import wave

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WHISPER_DIR = os.path.join(SCRIPT_DIR, "bin", "whisper")
MODEL_DEFAULT = os.path.join(WHISPER_DIR, "models", "ggml-tiny.bin")
BACKENDS_DIR = os.path.join(WHISPER_DIR, "lib", "ggml", "backends0")
LIB_DIR = os.path.join(WHISPER_DIR, "lib")
WL_COPY_BIN = os.path.join(SCRIPT_DIR, "bin", "wl-copy")

UID_VAL = os.getuid()
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
PID_FILE = os.path.join(RUNTIME_DIR, f"logipop_dictation_{UID_VAL}.pid")
HELD_FILE = os.path.join(RUNTIME_DIR, f"logipop_dictation_{UID_VAL}.held")
AUDIO_FILE = os.path.join(RUNTIME_DIR, f"logipop_dictation_{UID_VAL}.wav")
DAEMON_SOCK = os.path.join(RUNTIME_DIR, f"logipop_emoji_{UID_VAL}.sock")

SOUND_START = "/usr/share/sounds/freedesktop/stereo/bell.oga"
SOUND_STOP = "/usr/share/sounds/freedesktop/stereo/complete.oga"

# Parámetros de detección de voz y silencio (VAD)
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 1600         # 100 ms por bloque de audio a 16kHz
CHUNK_BYTES = CHUNK_SAMPLES * 2  # 16-bit mono = 3200 bytes por bloque
CHUNK_DURATION = 0.1         # 0.1 segundos
INITIAL_SILENCE_LIMIT = 3.5  # Si no hay voz en los primeros 3.5s, se auto-cancela
SPEECH_SILENCE_LIMIT = 1.2   # 1.2s de silencio tras hablar detiene la grabación automáticamente
MAX_RECORDING_LIMIT = 35.0   # Límite máximo absoluto de seguridad (35s)
BASE_MIN_THRESHOLD = 4500.0  # Umbral mínimo de energía para detectar voz humana

def play_sound(sound_path: str):
    """Reproduce un sonido de notificación breve sin bloquear el hilo principal."""
    if not os.path.exists(sound_path):
        return
    for player in ["pw-play", "paplay", "aplay"]:
        if shutil.which(player):
            try:
                subprocess.Popen([player, sound_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception:
                pass

def show_notification(title: str, message: str, expire_ms: int = 1800):
    """Muestra una notificación efímera en el escritorio que expira y no se acumula en la bandeja."""
    if shutil.which("notify-send"):
        try:
            cmd = [
                "notify-send",
                "-e",  # --transient: evita que persista o se guarde en la bandeja de notificaciones
                "-u", "low",  # Prioridad baja para que no bloquee ni acumule alertas
                "-h", "string:x-canonical-private-synchronous:logipop_dictate",
                "-h", "boolean:transient:true",
                "-t", str(expire_ms),
                "-a", "LogiPop Dictado",
                title,
                message
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def copy_to_clipboard(text: str) -> bool:
    """Copia texto al portapapeles (CLIPBOARD y PRIMARY) de forma nativa en Wayland/X11."""
    copied = False
    wl_bin = WL_COPY_BIN if os.path.isfile(WL_COPY_BIN) and os.access(WL_COPY_BIN, os.X_OK) else "wl-copy"
    try:
        subprocess.run([wl_bin, "-n", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0, check=True)
        subprocess.run([wl_bin, "-p", "-n", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
        copied = True
    except Exception:
        pass

    # Respaldo X11: xclip / xsel
    for sel in ["clipboard", "primary"]:
        for cmd in [["xclip", "-selection", sel], ["xsel", "-b" if sel == "clipboard" else "-p", "-i"]]:
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p.communicate(input=text.encode("utf-8"), timeout=0.5)
                copied = True
                break
            except Exception:
                pass

    return copied

def get_best_backend(backends_path: str) -> str:
    """Selecciona la librería de backend CPU óptima según las capacidades del procesador."""
    flags = set()
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("flags"):
                    flags = set(line.split(":")[1].split())
                    break
    except Exception:
        pass

    candidates = []
    if "avx2" in flags and "fma" in flags:
        candidates.append("libggml-cpu-haswell.so")
    if "sse4_2" in flags:
        candidates.append("libggml-cpu-sse42.so")
    candidates.append("libggml-cpu-x64.so")

    for cand in candidates:
        full_path = os.path.join(backends_path, cand)
        if os.path.isfile(full_path):
            return full_path

    try:
        for fname in os.listdir(backends_path):
            if fname.endswith(".so"):
                return os.path.join(backends_path, fname)
    except Exception:
        pass
    return ""

def clean_whisper_text(raw_text: str) -> str:
    """Limpia la transcripción eliminando alucinaciones comunes de silencio y marcadores de audio."""
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    if not re.search(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]', cleaned):
        return ""
    return cleaned

def send_to_daemon(command: str) -> bool:
    """Envía un comando al socket UNIX del demonio de LogiPop."""
    if not os.path.exists(DAEMON_SOCK):
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(DAEMON_SOCK)
        sock.sendall((command + "\n").encode("utf-8"))
        sock.close()
        return True
    except Exception:
        return False

def is_recording_active() -> int:
    """Devuelve el PID del proceso de grabación si está activo, o 0 si no."""
    if not os.path.exists(PID_FILE):
        return 0
    try:
        with open(PID_FILE, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        return 0

def run_dictation_session():
    """Inicia sesión de dictado con detección de silencio automática y auto-pegado."""
    # 1. Registrar PID actual
    my_pid = os.getpid()
    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(my_pid))

    rec_proc = None
    stop_requested = False

    def handle_stop(signum, frame):
        nonlocal stop_requested, rec_proc
        stop_requested = True
        if rec_proc is not None:
            try:
                rec_proc.terminate()
            except Exception:
                pass

    signal.signal(signal.SIGUSR1, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    # 2. Reproducir tono inicial de aviso y mostrar notificación
    play_sound(SOUND_START)
    show_notification(
        "🎙️ Dictado: Escuchando...",
        "Habla ahora. Se detendrá automáticamente al terminar de hablar.",
        2000
    )
    # Pausa breve (250ms) para que el tono del altavoz termine y no sea captado por el micrófono
    time.sleep(0.25)

    # 3. Iniciar comando de captura de audio en streaming
    if shutil.which("pw-record"):
        rec_cmd = ["pw-record", "--rate", str(SAMPLE_RATE), "--channels", "1", "--format", "s16", "--container", "raw", "-"]
    elif shutil.which("ffmpeg"):
        rec_cmd = ["ffmpeg", "-f", "pulse", "-i", "default", "-ar", str(SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"]
    else:
        show_notification("❌ Error de Grabación", "No se encontró pw-record ni ffmpeg en el sistema.")
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        return

    try:
        rec_proc = subprocess.Popen(
            rec_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    except Exception as e:
        show_notification("❌ Error", f"No se pudo iniciar el grabador de audio: {e}")
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        return

    # 4. Preparar archivo de audio WAV
    if os.path.exists(AUDIO_FILE):
        try:
            os.unlink(AUDIO_FILE)
        except Exception:
            pass

    try:
        wf = wave.open(AUDIO_FILE, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
    except Exception as e:
        rec_proc.terminate()
        show_notification("❌ Error", f"No se pudo crear archivo WAV: {e}")
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        return

    # 5. Bucle de captura con VAD (Voice Activity Detection)
    initial_rms_samples = []
    speech_started = False
    speech_chunks_count = 0
    silence_chunks_count = 0
    total_duration = 0.0
    threshold = BASE_MIN_THRESHOLD

    try:
        while not stop_requested:
            chunk = rec_proc.stdout.read(CHUNK_BYTES)
            if not chunk or len(chunk) < CHUNK_BYTES:
                break

            wf.writeframes(chunk)
            total_duration += CHUNK_DURATION

            # Calcular RMS de energía AC del bloque actual
            samples = struct.unpack(f"<{CHUNK_SAMPLES}h", chunk)
            avg = sum(samples) / CHUNK_SAMPLES
            rms = math.sqrt(sum((s - avg) ** 2 for s in samples) / CHUNK_SAMPLES)

            # Calibración del ruido ambiente en los primeros 4 bloques (400ms)
            if len(initial_rms_samples) < 4:
                initial_rms_samples.append(rms)
                if len(initial_rms_samples) == 4:
                    ambient = sum(initial_rms_samples) / 4.0
                    threshold = max(ambient * 1.45, BASE_MIN_THRESHOLD)

            # Verificar si la tecla está físicamente mantenida presionada (Hold-to-Talk)
            key_is_held = os.path.exists(HELD_FILE)

            # Fase 1: Esperando que el usuario comience a hablar
            if not speech_started:
                if rms >= threshold:
                    speech_chunks_count += 1
                    # Requiere 2 bloques consecutivos (~200ms) de energía sostenida
                    if speech_chunks_count >= 2:
                        speech_started = True
                        silence_chunks_count = 0
                else:
                    speech_chunks_count = 0
                    # Si la tecla NO está presionada y pasan 3.5 segundos sin hablar, auto-cancelar
                    if not key_is_held and total_duration >= INITIAL_SILENCE_LIMIT:
                        break

            # Fase 2: Voz detectada, monitoreando el silencio posterior
            else:
                if key_is_held:
                    # MIENTRAS LA TECLA ESTÉ PRESIONADA: PERMANECER ESCUCHANDO SIEMPRE
                    silence_chunks_count = 0
                else:
                    if rms < threshold:
                        silence_chunks_count += 1
                        # Si hay silencio continuo por SPEECH_SILENCE_LIMIT (1.2s), terminar
                        if (silence_chunks_count * CHUNK_DURATION) >= SPEECH_SILENCE_LIMIT:
                            break
                    else:
                        silence_chunks_count = 0

            # Límite máximo de seguridad absoluto
            if total_duration >= MAX_RECORDING_LIMIT:
                break
    finally:
        wf.close()
        try:
            rec_proc.terminate()
            rec_proc.wait(timeout=0.6)
        except Exception:
            try:
                rec_proc.kill()
            except Exception:
                pass

        try:
            if os.path.exists(PID_FILE):
                os.unlink(PID_FILE)
            if os.path.exists(HELD_FILE):
                os.unlink(HELD_FILE)
        except Exception:
            pass

    # 6. Evaluar si hubo voz
    if not speech_started and not stop_requested:
        if os.path.exists(AUDIO_FILE):
            try:
                os.unlink(AUDIO_FILE)
            except Exception:
                pass
        show_notification("⚠️ No se detectó voz", "No se detectó actividad de voz.", 1500)
        return

    # Verificar que el archivo de audio tenga contenido útil
    if not os.path.exists(AUDIO_FILE) or os.path.getsize(AUDIO_FILE) < 1000:
        show_notification("⚠️ Audio demasiado corto", "No se registró suficiente audio para procesar.", 1500)
        return

    play_sound(SOUND_STOP)
    show_notification("⚙️ Transcribiendo...", "Procesando voz con Whisper local...", 1500)

    # 7. Localizar binario y modelo de Whisper
    whisper_bin = os.path.join(WHISPER_DIR, "whisper-cli")
    if not (os.path.isfile(whisper_bin) and os.access(whisper_bin, os.X_OK)):
        whisper_bin = shutil.which("whisper-cli") or shutil.which("whisper")

    model_path = MODEL_DEFAULT
    if not os.path.isfile(model_path):
        for candidate in ["/usr/share/whisper.cpp-models/ggml-tiny.bin", os.path.expanduser("~/.cache/whisper/ggml-tiny.bin")]:
            if os.path.isfile(candidate):
                model_path = candidate
                break

    if not whisper_bin or not os.path.isfile(model_path):
        show_notification("⚠️ Whisper no instalado", "Ejecuta setup_whisper.sh para descargar el motor local.", 4000)
        return

    env = os.environ.copy()
    if os.path.isdir(LIB_DIR):
        env["LD_LIBRARY_PATH"] = f"{LIB_DIR}:{env.get('LD_LIBRARY_PATH', '')}"

    if os.path.isdir(BACKENDS_DIR):
        best_backend = get_best_backend(BACKENDS_DIR)
        if best_backend:
            env["GGML_BACKEND_PATH"] = best_backend

    cmd = [
        whisper_bin,
        "-m", model_path,
        "-l", "es",
        "-nt",
        "-np",
        "-f", AUDIO_FILE
    ]

    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
        raw_output = res.stdout
    except subprocess.TimeoutExpired:
        show_notification("⏱️ Tiempo agotado", "La transcripción tomó más de 25 segundos.", 2500)
        return
    except Exception as e:
        show_notification("❌ Error al transcribir", str(e), 3000)
        return

    clean_text = clean_whisper_text(raw_output)

    # 8. Copiado automático al portapapeles e inyección instantánea (Ctrl+V)
    if clean_text:
        # A. Copiar inmediatamente al portapapeles (CLIPBOARD y PRIMARY)
        copy_to_clipboard(clean_text)

        # B. Enviar comando de pegado al demonio de teclado virtual (/dev/uinput)
        pasted = send_to_daemon(f"paste:{clean_text}")

        # C. Notificación al usuario
        display_preview = clean_text if len(clean_text) <= 50 else (clean_text[:47] + "...")
        if pasted:
            show_notification("✅ Transcrito y Pegado:", f"«{display_preview}»", 1800)
        else:
            show_notification("📋 Copiado al Portapapeles:", f"«{display_preview}»\n(Pega con Ctrl+V)", 2000)
    else:
        show_notification("⚠️ No se detectó voz", "Intenta hablar más cerca del micrófono.", 1500)

def toggle_recording():
    """Alterna entre iniciar con VAD o detener manualmente de inmediato."""
    active_pid = is_recording_active()
    if active_pid > 0:
        # Si ya está grabando, la segunda pulsación detiene manualmente de inmediato
        try:
            os.kill(active_pid, signal.SIGUSR1)
        except OSError:
            pass
    else:
        # Primera pulsación: arranca grabación con detección de silencio automática
        run_dictation_session()

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "toggle"
    if action == "toggle":
        toggle_recording()
    elif action == "start":
        if is_recording_active() == 0:
            run_dictation_session()
    elif action == "stop":
        active_pid = is_recording_active()
        if active_pid > 0:
            try:
                os.kill(active_pid, signal.SIGUSR1)
            except OSError:
                pass
    elif action == "status":
        active = is_recording_active()
        print(f"Recording active: {active > 0} (PID: {active})")
    else:
        print(f"Uso: {sys.argv[0]} [toggle|start|stop|status]")

if __name__ == "__main__":
    main()
