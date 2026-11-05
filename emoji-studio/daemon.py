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

def get_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime_dir, f"logipop_emoji_{os.getuid()}.sock")

def load_emojis():
    emojis = DEFAULT_EMOJIS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                emojis.update(json.load(f))
        except Exception:
            pass
    return emojis

def copy_to_clipboard(text: str):
    """Copia texto al portapapeles de forma persistente y nativa en Wayland."""
    # 1. Prioridad: wl-copy local o del sistema (funciona 100% en segundo plano en Wayland)
    wl_bin = WL_COPY_BIN if os.path.isfile(WL_COPY_BIN) and os.access(WL_COPY_BIN, os.X_OK) else "wl-copy"
    try:
        p = subprocess.Popen([wl_bin, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        ecodes.KEY_SEMICOLON
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
    server.listen(5)
    os.chmod(socket_path, 0o600)

    print("LogiPop Daemon iniciado y listo para recibir peticiones.")

    try:
        while True:
            conn, _ = server.accept()
            try:
                data = conn.recv(64).decode("utf-8").strip()
                if not data:
                    conn.close()
                    continue

                if data == "5":
                    # Selector de emojis de GNOME: Super + .
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 1)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_DOT, 1)
                    ui.syn()
                    time.sleep(0.03)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_DOT, 0)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTMETA, 0)
                    ui.syn()
                elif data in ["1", "2", "3", "4"]:
                    emojis = load_emojis()
                    target_emoji = emojis.get(data, "😊")

                    # 1. Copiar al portapapeles
                    copy_to_clipboard(target_emoji)

                    # Pequeña pausa para asegurar que el portapapeles esté registrado
                    time.sleep(0.02)

                    # 2. Simular Ctrl + V
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
                    ui.syn()
                    time.sleep(0.03)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
                    ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
                    ui.syn()

                conn.sendall(b"OK\n")
            except Exception as e:
                pass
            finally:
                conn.close()
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
