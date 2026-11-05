#!/usr/bin/env python3
"""
send_emoji.py - Inyector de emojis para Logitech POP Keys
Maneja la inserción rápida de los 4 emojis personalizados (copiar + pegar)
y la invocación del selector general de emojis para la 5ta tecla.
"""

import sys
import json
import os
import time

# Verificación de plataforma: exclusivo para Linux
if not sys.platform.startswith("linux"):
    sys.exit("Error: send_emoji.py es exclusivo para sistemas Linux.")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "emojis.json")

DEFAULT_EMOJIS = {
    "1": "😍",
    "2": "😂",
    "3": "😊",
    "4": "🔥"
}

def emit_keypress(keys_down, keys_up=None, delay=0.04):
    """Emite una combinación de teclas mediante /dev/uinput."""
    try:
        import evdev
        from evdev import ecodes

        all_keys = list(set(keys_down + (keys_up or keys_down)))
        cap = {ecodes.EV_KEY: all_keys}
        ui = evdev.UInput(cap, name="logipop-uinput")

        # Presionar teclas
        for k in keys_down:
            ui.write(ecodes.EV_KEY, k, 1)
        ui.syn()

        time.sleep(delay)

        # Liberar teclas
        for k in (keys_up or keys_down):
            ui.write(ecodes.EV_KEY, k, 0)
        ui.syn()

        ui.close()
        return True
    except Exception as e:
        return False

def open_emoji_picker():
    """Abre el selector de emojis del sistema (Super + . o Ctrl + .)."""
    try:
        import evdev
        from evdev import ecodes
        emit_keypress([ecodes.KEY_LEFTMETA, ecodes.KEY_DOT])
    except Exception:
        pass

def paste_emoji(emoji_char: str):
    """Copia el emoji al portapapeles y simula Ctrl+V para pegarlo."""
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gtk, Gdk

    # Crear ventana invisible para anclar conexión Wayland/X11
    win = Gtk.Invisible()
    win.show()

    display = Gdk.Display.get_default()
    clip = Gtk.Clipboard.get_default(display)
    clip.set_text(emoji_char, -1)
    clip.store()

    # Procesar eventos para asegurar que el portapapeles lo tiene
    for _ in range(10):
        Gtk.main_iteration_do(False)

    # Simular Ctrl + V
    try:
        import evdev
        from evdev import ecodes
        emit_keypress([ecodes.KEY_LEFTCTRL, ecodes.KEY_V])
    except Exception:
        pass

    # Mantener el bucle vivo brevemente (~1 segundo) para que la aplicación en foco
    # pueda leer el contenido del portapapeles bajo Wayland
    start_time = time.time()
    while time.time() - start_time < 1.0:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(0.04)

def main():
    if len(sys.argv) < 2:
        print("Uso: send_emoji.py <1|2|3|4|5>")
        sys.exit(1)

    key_index = sys.argv[1].strip()

    if key_index == "5":
        open_emoji_picker()
        return

    # Cargar emoji configurado
    emojis = DEFAULT_EMOJIS.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                emojis.update(json.load(f))
        except Exception:
            pass

    target_emoji = emojis.get(key_index, "😊")
    paste_emoji(target_emoji)

if __name__ == "__main__":
    main()
