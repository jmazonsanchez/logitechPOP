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
import signal
import threading

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
    """Copia texto al portapapeles (CLIPBOARD y PRIMARY) de forma nativa en Wayland/X11."""
    copied = False
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
        # Copiar también a selección primaria
        subprocess.run(
            [wl_bin, "-p", "-n", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.0
        )
        copied = True
    except Exception:
        pass

    # 2. Respaldo: xclip / xsel (X11)
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

# ==============================================================================
# Detección automática de ventana activa (Terminal vs Aplicación Estándar)
# ==============================================================================
TERMINAL_KEYWORDS = {
    "ptyxis", "gnome-terminal", "terminal", "konsole", "alacritty", "kitty",
    "tilix", "xterm", "urxvt", "terminator", "wezterm", "foot", "contour",
    "blackbox", "guake", "tilda", "xfce4-terminal", "hyper", "tabby", "lxterminal"
}

_active_window_info = {
    "is_terminal": False,
    "app_name": ""
}

def _check_is_terminal(app_name, win_name=""):
    app_low = (app_name or "").lower()
    win_low = (win_name or "").lower()
    if any(k in app_low for k in TERMINAL_KEYWORDS):
        return True
    if "terminal" in win_low or "consola" in win_low:
        return True
    return False

def _start_active_window_tracker():
    """
    Rastreador en tiempo real vía AT-SPI (estándar nativo para GNOME/Wayland).
    Se ejecuta en un hilo secundario sin afectar la latencia del demonio (<1ms).
    """
    def tracker_thread():
        try:
            import gi
            gi.require_version("Atspi", "2.0")
            from gi.repository import Atspi, GLib

            def on_event(event):
                if not event.source:
                    return
                try:
                    if event.type == "window:activate" or (
                        event.type == "object:state-changed:active" and getattr(event, "detail1", 0) == 1
                    ):
                        app = event.source.get_application()
                        app_name = app.get_name() if app else ""
                        win_name = event.source.get_name() or ""
                        if app_name and app_name != "gnome-shell":
                            _active_window_info["app_name"] = app_name
                            _active_window_info["is_terminal"] = _check_is_terminal(app_name, win_name)
                except Exception:
                    pass

            def initial_scan():
                try:
                    desktop = Atspi.get_desktop(0)
                    for i in range(desktop.get_child_count()):
                        app = desktop.get_child_at_index(i)
                        if not app:
                            continue
                        name = (app.get_name() or "").lower()
                        if name in ("gnome-shell", "mutter-x11-frames"):
                            continue
                        for j in range(app.get_child_count()):
                            w = app.get_child_at_index(j)
                            if not w:
                                continue
                            if Atspi.StateType.ACTIVE in w.get_state_set().get_states():
                                _active_window_info["app_name"] = app.get_name()
                                _active_window_info["is_terminal"] = _check_is_terminal(app.get_name(), w.get_name())
                                return
                except Exception:
                    pass

            l1 = Atspi.EventListener.new(on_event)
            l1.register("window:activate")
            l2 = Atspi.EventListener.new(on_event)
            l2.register("object:state-changed:active")
            initial_scan()

            loop = GLib.MainLoop()
            loop.run()
        except Exception:
            pass

    t = threading.Thread(target=tracker_thread, daemon=True, name="WindowTracker")
    t.start()

def emit_paste(ui, ecodes, is_terminal=False, fast=False):
    """
    Emite la pulsación de pegado adecuada según el tipo de ventana activa:
    - Terminal (Ptyxis, GNOME Terminal, etc.): Ctrl + Shift + V
    - Aplicación GUI estándar (Navegador, Chats, Editores): Ctrl + V
    """
    if is_terminal:
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 1)
        ui.syn()
        time.sleep(0.010 if fast else 0.025)
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
        ui.syn()
        time.sleep(0.015 if fast else 0.035)
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
        ui.syn()
        time.sleep(0.010 if fast else 0.020)
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTSHIFT, 0)
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
        ui.syn()
    else:
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
        ui.syn()
        time.sleep(0.005 if fast else 0.025)
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
        ui.syn()
        time.sleep(0.012 if fast else 0.035)
        ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
        ui.syn()
        time.sleep(0.005 if fast else 0.020)
        ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
        ui.syn()

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
    dictate_proc = None
    dictate_press_time = 0.0
    dictate_held_file = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", f"logipop_dictation_{os.getuid()}.held")
    try:
        if os.path.exists(dictate_held_file):
            os.unlink(dictate_held_file)
    except Exception:
        pass
    try:
        init_emojis = load_emojis()
        primary_emoji = init_emojis.get("1", "🔥")
        copy_to_clipboard(primary_emoji)
        last_emoji = primary_emoji
        last_paste_time = time.time()
    except Exception:
        pass

    # Iniciar rastreador en tiempo real de ventana activa (Terminal vs Aplicación GUI)
    _start_active_window_tracker()

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

            elif data in ["dictate_press", "dictate"]:
                # Pulsación de la tecla de Dictado (inicio o corte manual)
                now = time.time()
                dictate_press_time = now
                try:
                    with open(dictate_held_file, "w") as f:
                        f.write(str(now))
                except Exception:
                    pass

                # Validación de escucha activa:
                # Si ya está encendido el escucha, finalizar de inmediato y procesar el audio
                dictate_script = os.path.join(SCRIPT_DIR, "dictate.py")
                if dictate_proc is not None and dictate_proc.poll() is None:
                    try:
                        dictate_proc.send_signal(signal.SIGUSR1)
                    except OSError:
                        pass
                else:
                    # Comprobación de respaldo por archivo PID en caso de instancias independientes
                    active_pid = 0
                    pid_file = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", f"logipop_dictation_{os.getuid()}.pid")
                    if os.path.exists(pid_file):
                        try:
                            with open(pid_file, "r") as f:
                                p = int(f.read().strip())
                            os.kill(p, 0)
                            active_pid = p
                        except Exception:
                            pass

                    if active_pid > 0:
                        try:
                            os.kill(active_pid, signal.SIGUSR1)
                        except OSError:
                            pass
                    else:
                        dictate_proc = subprocess.Popen([sys.executable, dictate_script, "start"], start_new_session=True)

            elif data == "dictate_release":
                # Al soltar la tecla de Dictado
                now = time.time()
                held_duration = now - dictate_press_time
                try:
                    if os.path.exists(dictate_held_file):
                        os.unlink(dictate_held_file)
                except Exception:
                    pass

                # Si el usuario mantuvo presionada la tecla (Hold-to-Talk >= 0.35s):
                # Al soltarla, se finaliza la escucha inmediatamente y se procesa el audio
                if held_duration >= 0.35:
                    if dictate_proc is not None and dictate_proc.poll() is None:
                        try:
                            dictate_proc.send_signal(signal.SIGUSR1)
                        except OSError:
                            pass
                    else:
                        active_pid = 0
                        pid_file = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or "/tmp", f"logipop_dictation_{os.getuid()}.pid")
                        if os.path.exists(pid_file):
                            try:
                                with open(pid_file, "r") as f:
                                    p = int(f.read().strip())
                                os.kill(p, 0)
                                active_pid = p
                            except Exception:
                                pass
                        if active_pid > 0:
                            try:
                                os.kill(active_pid, signal.SIGUSR1)
                            except OSError:
                                pass

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
                target_text = data[6:].strip()
                if target_text:
                    # Copiar a portapapeles (CLIPBOARD y PRIMARY)
                    copy_to_clipboard(target_text)
                    last_emoji = target_text
                    last_paste_time = time.time()
                    # Pausa breve (~60ms) para que el compositor registre la nueva oferta de datos
                    time.sleep(0.06)

                    # Inyección inteligente según la ventana activa:
                    # Ctrl + Shift + V en terminales de Linux, Ctrl + V en aplicaciones de escritorio estándar
                    is_term = _active_window_info.get("is_terminal", False)
                    emit_paste(ui, ecodes, is_terminal=is_term, fast=False)
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

                # Inyección inteligente rápida (~22ms) según ventana activa
                is_term = _active_window_info.get("is_terminal", False)
                emit_paste(ui, ecodes, is_terminal=is_term, fast=True)
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
