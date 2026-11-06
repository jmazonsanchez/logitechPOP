#!/usr/bin/env python3
"""
daemon.py - Demonio en segundo plano de LogiPop Emoji Studio
Mantiene abierto el teclado virtual /dev/uinput y gestiona el portapapeles
para garantizar inserción instantánea (<10ms) de emojis en Wayland y X11.
"""

import os
import sys
import time
import json
import socket
import select
import subprocess

# Plataforma exclusiva Linux
if not sys.platform.startswith("linux"):
    sys.exit(0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "emojis.json")
WL_COPY_BIN = os.path.join(SCRIPT_DIR, "bin", "wl-copy")

DEFAULT_EMOJIS = {
    "1": "😍",
    "2": "😂",
    "3": "😊",
    "4": "🔥"
}

_cached_emojis = None
_cached_mtime = 0

def get_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime_dir, f"logipop_emoji_{os.getuid()}.sock")

def load_emojis():
    """Carga configuración con caché en memoria basado en mtime para latencia 0."""
    global _cached_emojis, _cached_mtime
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_EMOJIS.copy()

    try:
        mtime = os.path.getmtime(CONFIG_FILE)
        if _cached_emojis is not None and mtime == _cached_mtime:
            return _cached_emojis

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            emojis = {**DEFAULT_EMOJIS, **cfg}
            _cached_emojis = emojis
            _cached_mtime = mtime
            return emojis
    except Exception:
        return _cached_emojis or DEFAULT_EMOJIS.copy()

def copy_to_clipboard(text: str) -> bool:
    """Copia texto al portapapeles de forma sincrónica y nativa en Wayland/X11."""
    # 1. Prioridad: wl-copy local o del sistema en Wayland
    wl_bin = WL_COPY_BIN if os.path.isfile(WL_COPY_BIN) and os.access(WL_COPY_BIN, os.X_OK) else "wl-copy"
    try:
        subprocess.run(
            [wl_bin, "-n", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.0,
            check=True
        )
        return True
    except Exception:
        pass

    # 2. Respaldo: xclip / xsel (X11)
    for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]]:
        try:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode("utf-8"), timeout=0.5)
            return True
        except Exception:
            pass

    return False

def main():
    import evdev
    from evdev import ecodes

    socket_path = get_socket_path()

    # Si ya existe el socket, verificar si hay otra instancia viva
    if os.path.exists(socket_path):
        try:
            test_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            test_sock.connect(socket_path)
            test_sock.close()
            # Ya hay un demonio corriendo
            print("LogiPop Daemon ya se encuentra en ejecución.")
            return
        except Exception:
            try:
                os.unlink(socket_path)
            except Exception:
                pass

    # Crear el dispositivo de teclado virtual persistente
    needed_keys = [
        ecodes.KEY_LEFTCTRL,
        ecodes.KEY_V,
        ecodes.KEY_LEFTMETA,
        ecodes.KEY_DOT,
        ecodes.KEY_SEMICOLON,
        ecodes.KEY_MICMUTE,
        ecodes.KEY_D,
        ecodes.KEY_P,
        ecodes.KEY_SWITCHVIDEOMODE,
        ecodes.KEY_SYSRQ,
        ecodes.KEY_LEFTSHIFT
    ]
    cap = {ecodes.EV_KEY: needed_keys}

    try:
        ui = evdev.UInput(cap, name="LogiPop Virtual Keyboard")
    except Exception as e:
        print(f"Error al inicializar /dev/uinput: {e}")
        return

    # Crear servidor socket UNIX
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)
    server.listen(10)
    os.chmod(socket_path, 0o600)

    # Estado del portapapeles y pre-calentamiento
    last_emoji = None
    last_paste_time = 0.0
    last_screen_time = 0.0
    try:
        init_emojis = load_emojis()
        primary_emoji = init_emojis.get("1", "🔥")
        copy_to_clipboard(primary_emoji)
        last_emoji = primary_emoji
        last_paste_time = time.time()
    except Exception:
        pass

    print("LogiPop Daemon ultrarrápido iniciado y listo.")

    try:
        while True:
            conn, _ = server.accept()
            try:
                data = conn.recv(8192).decode("utf-8").strip()
            except Exception:
                data = ""
            finally:
                # Cierre inmediato de la conexión para liberar al cliente en < 1ms
                try:
                    conn.close()
                except Exception:
                    pass

            if not data:
                continue

            if data == "reload":
                # Recargar configuración y pre-calentar portapapeles con Tecla 1
                try:
                    global _cached_emojis, _cached_mtime
                    _cached_emojis = None
                    _cached_mtime = 0
                    emojis = load_emojis()
                    primary_emoji = emojis.get("1", "🔥")
                    copy_to_clipboard(primary_emoji)
                    last_emoji = primary_emoji
                    last_paste_time = time.time()
                except Exception:
                    pass
                continue

            if data == "5":
                # Selector Mini Flotante de LogiPop (Tecla 5)
                # Si ya está abierto, se cierra (comportamiento toggle); si no, se despliega
                picker_script = os.path.join(SCRIPT_DIR, "picker.py")
                try:
                    res = subprocess.run(["pgrep", "-f", "picker.py"], capture_output=True, text=True)
                    if res.stdout.strip():
                        subprocess.run(["pkill", "-f", "picker.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        subprocess.Popen(["python3", picker_script], start_new_session=True)
                except Exception:
                    subprocess.Popen(["python3", picker_script], start_new_session=True)

            elif data == "micmute":
                # Silenciar / Desmutear micrófono a nivel de sistema y disparar OSD en GNOME
                ui.write(ecodes.EV_KEY, ecodes.KEY_MICMUTE, 1)
                ui.syn()
                time.sleep(0.012)
                ui.write(ecodes.EV_KEY, ecodes.KEY_MICMUTE, 0)
                ui.syn()

            elif data == "dictate":
                # Dictado por voz (Toggle) mediante Whisper.cpp local y PipeWire
                dictate_script = os.path.join(SCRIPT_DIR, "dictate.py")
                subprocess.Popen(["python3", dictate_script, "toggle"], start_new_session=True)

            elif data in ["screenshot_full", "screenshot-full"]:
                # Captura de pantalla completa automática (Shift + Print)
                now = time.time()
                if (now - last_screen_time) < 0.35:
                    continue
                last_screen_time = now
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
                ui.syn()
                time.sleep(0.02)
                ui.write(ecodes.EV_KEY, ecodes.KEY_SYSRQ, 1)
                ui.syn()
                time.sleep(0.035)
                ui.write(ecodes.EV_KEY, ecodes.KEY_SYSRQ, 0)
                ui.syn()
                time.sleep(0.015)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
                ui.syn()

            elif data in ["screenshot_area", "screenshot-area", "screenshot"]:
                # Selector interactivo de recorte de pantalla (Print)
                now = time.time()
                if (now - last_screen_time) < 0.35:
                    continue
                last_screen_time = now
                ui.write(ecodes.EV_KEY, ecodes.KEY_SYSRQ, 1)
                ui.syn()
                time.sleep(0.035)
                ui.write(ecodes.EV_KEY, ecodes.KEY_SYSRQ, 0)
                ui.syn()

            elif data in ["screen", "project"]:
                now = time.time()
                if (now - last_screen_time) < 0.35:
                    continue
                last_screen_time = now
                # Proyectar / Cambiar monitor o entrada de pantalla (Super + P / Switch Monitor)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 1)
                ui.syn()
                time.sleep(0.02)
                ui.write(ecodes.EV_KEY, ecodes.KEY_P, 1)
                ui.syn()
                time.sleep(0.035)
                ui.write(ecodes.EV_KEY, ecodes.KEY_P, 0)
                ui.syn()
                time.sleep(0.015)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 0)
                ui.syn()

            elif data == "showdesktop":
                # Minimizar / Restaurar ventanas (Super + D - Mostrar Escritorio)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 1)
                ui.write(ecodes.EV_KEY, ecodes.KEY_D, 1)
                ui.syn()
                time.sleep(0.015)
                ui.write(ecodes.EV_KEY, ecodes.KEY_D, 0)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 0)
                ui.syn()

            elif data == "overview":
                # Vista de Actividades de GNOME (Super)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 1)
                ui.syn()
                time.sleep(0.015)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 0)
                ui.syn()

            elif data.startswith("paste:"):
                target_emoji = data[6:].strip()
                if target_emoji:
                    # Pausa breve (~70ms) para que GNOME Mutter devuelva el foco a la ventana anterior
                    time.sleep(0.07)
                    copy_to_clipboard(target_emoji)
                    last_emoji = target_emoji
                    last_paste_time = time.time()

                    # Simular Ctrl + V para insertar en la ventana activa previa
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
                    ui.syn()
                    time.sleep(0.005)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
                    ui.syn()
                    time.sleep(0.012)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
                    ui.syn()
                    time.sleep(0.005)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
                    ui.syn()
            elif data in ["1", "2", "3", "4"]:
                emojis = load_emojis()
                target_emoji = emojis.get(data, "😊")
                now = time.time()

                # Si es la misma tecla pulsada en ráfaga (últimos 3s), omitir wl-copy (latencia instantánea ~22ms)
                # Si es un emoji distinto o pasaron más de 3s (posible copia externa), actualizar portapapeles
                if target_emoji != last_emoji or (now - last_paste_time) > 3.0:
                    copy_to_clipboard(target_emoji)
                    last_emoji = target_emoji

                last_paste_time = now

                # Simulación de Ctrl + V de alta respuesta (~22ms)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
                ui.syn()
                time.sleep(0.005)
                ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
                ui.syn()
                time.sleep(0.012)
                ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
                ui.syn()
                time.sleep(0.005)
                ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
                ui.syn()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            ui.close()
        except Exception:
            pass
        try:
            server.close()
            os.unlink(socket_path)
        except Exception:
            pass

if __name__ == "__main__":
    main()
