#!/usr/bin/env python3
"""
dictate.py - Módulo de Dictado por Voz Offline para Logitech POP Keys
Utiliza Whisper.cpp local y PipeWire para transcripción de voz a texto privada,
sin conexión a internet y con inyección instantánea en Wayland y X11.
"""

import os
import sys
import time
import shutil
import signal
import subprocess
import re
import socket

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WHISPER_DIR = os.path.join(SCRIPT_DIR, "bin", "whisper")
MODEL_DEFAULT = os.path.join(WHISPER_DIR, "models", "ggml-tiny.bin")
BACKENDS_DIR = os.path.join(WHISPER_DIR, "lib", "ggml", "backends0")
LIB_DIR = os.path.join(WHISPER_DIR, "lib")

UID_VAL = os.getuid()
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
PID_FILE = os.path.join(RUNTIME_DIR, f"logipop_dictation_{UID_VAL}.pid")
AUDIO_FILE = os.path.join(RUNTIME_DIR, f"logipop_dictation_{UID_VAL}.wav")
DAEMON_SOCK = os.path.join(RUNTIME_DIR, f"logipop_emoji_{UID_VAL}.sock")

SOUND_START = "/usr/share/sounds/freedesktop/stereo/bell.oga"
SOUND_STOP = "/usr/share/sounds/freedesktop/stereo/complete.oga"

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

def show_notification(title: str, message: str, expire_ms: int = 3000):
    """Muestra una notificación en GNOME / escritorio reemplazando la anterior."""
    if shutil.which("notify-send"):
        try:
            cmd = [
                "notify-send",
                "-h", "string:x-canonical-private-synchronous:logipop_dictate",
                "-t", str(expire_ms),
                "-a", "LogiPop Dictado",
                title,
                message
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

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

    # Respaldo: primer .so disponible en backends0
    try:
        for fname in os.listdir(backends_path):
            if fname.endswith(".so"):
                return os.path.join(backends_path, fname)
    except Exception:
        pass
    return ""

def clean_whisper_text(raw_text: str) -> str:
    """Limpia la transcripción eliminando alucinaciones comunes de silencio y marcadores de audio."""
    # Eliminar marcadores entre corchetes o paréntesis como [MÚSICA], (risas), [BLANK_AUDIO]
    cleaned = re.sub(r'\[.*?\]', '', raw_text)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    # Normalizar espacios en blanco
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Si solo quedan signos de puntuación o puntos suspensivos sin letras/números, descartar
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
        # Verificar si el proceso con ese PID existe y está vivo
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError):
        # PID no válido o proceso terminado; limpiar archivo residual
        try:
            os.unlink(PID_FILE)
        except Exception:
            pass
        return 0

def start_recording():
    """Inicia la grabación de micrófono a 16kHz mono."""
    # Limpiar archivo de audio previo si existe
    if os.path.exists(AUDIO_FILE):
        try:
            os.unlink(AUDIO_FILE)
        except Exception:
            pass

    # Comando de grabación: pw-record prioritario, fallback a ffmpeg
    if shutil.which("pw-record"):
        cmd = ["pw-record", "--rate", "16000", "--channels", "1", "--format", "s16", AUDIO_FILE]
    elif shutil.which("ffmpeg"):
        cmd = ["ffmpeg", "-y", "-f", "pulse", "-i", "default", "-ar", "16000", "-ac", "1", AUDIO_FILE]
    else:
        show_notification("❌ Error de Grabación", "No se encontró pw-record ni ffmpeg en el sistema.")
        return

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        with open(PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(proc.pid))

        play_sound(SOUND_START)
        show_notification("🎙️ Dictado: Escuchando...", "Habla ahora. Presiona la tecla de nuevo para transcribir.", 4000)

        # Iniciar temporizador de seguridad de 35s en segundo plano para auto-detener
        watchdog_cmd = f"sleep 35 && python3 '{os.path.abspath(__file__)}' stop"
        subprocess.Popen(watchdog_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception as e:
        show_notification("❌ Error", f"No se pudo iniciar la grabación: {e}")

def stop_recording_and_transcribe():
    """Detiene la grabación, procesa el audio con Whisper y pega el resultado."""
    pid = is_recording_active()
    if pid > 0:
        try:
            # Enviar SIGINT para que el grabador cierre el archivo WAV con encabezado válido
            os.kill(pid, signal.SIGINT)
            # Esperar hasta 1 segundo a que el proceso termine
            for _ in range(10):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    break
        except Exception:
            pass

    # Eliminar PID file
    try:
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
    except Exception:
        pass

    play_sound(SOUND_STOP)

    # Verificar que el archivo de audio exista y tenga contenido
    if not os.path.exists(AUDIO_FILE) or os.path.getsize(AUDIO_FILE) < 1000:
        show_notification("⚠️ Audio demasiado corto", "No se registró suficiente audio para procesar.", 2000)
        return

    show_notification("⚙️ Transcribiendo...", "Procesando voz con Whisper local...", 3000)

    # Localizar binario de whisper-cli
    whisper_bin = os.path.join(WHISPER_DIR, "whisper-cli")
    if not (os.path.isfile(whisper_bin) and os.access(whisper_bin, os.X_OK)):
        whisper_bin = shutil.which("whisper-cli") or shutil.which("whisper")

    # Localizar modelo
    model_path = MODEL_DEFAULT
    if not os.path.isfile(model_path):
        for candidate in ["/usr/share/whisper.cpp-models/ggml-tiny.bin", os.path.expanduser("~/.cache/whisper/ggml-tiny.bin")]:
            if os.path.isfile(candidate):
                model_path = candidate
                break

    if not whisper_bin or not os.path.isfile(model_path):
        setup_script = os.path.join(SCRIPT_DIR, "bin", "setup_whisper.sh")
        show_notification("⚠️ Whisper no instalado", "Ejecuta setup_whisper.sh para descargar el motor local.", 4000)
        return

    # Preparar entorno para whisper-cli
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

    if clean_text:
        # Notificación con el texto transcrito
        display_preview = clean_text if len(clean_text) <= 50 else (clean_text[:47] + "...")
        show_notification("✅ Transcrito:", f"«{display_preview}»", 2500)

        # Inyectar texto vía el demonio de teclado virtual (paste:<texto>)
        if not send_to_daemon(f"paste:{clean_text}"):
            # Si el demonio no está activo, copiar al portapapeles con wl-copy
            wl_copy = os.path.join(SCRIPT_DIR, "bin", "wl-copy")
            if os.path.isfile(wl_copy):
                subprocess.run([wl_copy, "-n", clean_text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        show_notification("⚠️ No se detectó voz", "Intenta hablar más cerca del micrófono.", 2000)

def toggle_recording():
    """Alterna entre iniciar y detener la grabación."""
    if is_recording_active() > 0:
        stop_recording_and_transcribe()
    else:
        start_recording()

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "toggle"
    if action == "toggle":
        toggle_recording()
    elif action == "start":
        if is_recording_active() == 0:
            start_recording()
    elif action == "stop":
        if is_recording_active() > 0:
            stop_recording_and_transcribe()
    elif action == "status":
        active = is_recording_active()
        print(f"Recording active: {active > 0} (PID: {active})")
    else:
        print(f"Uso: {sys.argv[0]} [toggle|start|stop|status]")

if __name__ == "__main__":
    main()
