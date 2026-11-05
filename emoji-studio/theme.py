"""
theme.py - Gestor de Temas (Modo Oscuro / Modo Claro) para LogiPop
Detecta automáticamente el esquema de color del sistema (GNOME / FreeDesktop)
y actualiza dinámicamente el estilo visual en tiempo real.
"""

import sys
from gi.repository import Gtk, Gdk, Gio

def is_dark_mode() -> bool:
    """Comprueba si el sistema tiene activado el modo oscuro."""
    try:
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source and schema_source.lookup("org.gnome.desktop.interface", True):
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            color_scheme = settings.get_string("color-scheme")
            if "dark" in color_scheme.lower():
                return True
            gtk_theme = settings.get_string("gtk-theme")
            if "dark" in gtk_theme.lower():
                return True
    except Exception:
        pass

    try:
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings:
            if gtk_settings.get_property("gtk-application-prefer-dark-theme"):
                return True
            theme_name = gtk_settings.get_property("gtk-theme-name")
            if theme_name and "dark" in theme_name.lower():
                return True
    except Exception:
        pass

    return False

def setup_theme_listener(callback):
    """Escucha cambios en tiempo real del tema del sistema."""
    try:
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source and schema_source.lookup("org.gnome.desktop.interface", True):
            settings = Gio.Settings.new("org.gnome.desktop.interface")
            
            def _on_change(s, key):
                dark = is_dark_mode()
                callback(dark)

            settings.connect("changed::color-scheme", _on_change)
            settings.connect("changed::gtk-theme", _on_change)
            return settings
    except Exception:
        pass
    return None

def get_manager_css(is_dark: bool) -> bytes:
    if is_dark:
        return b"""
        window {
            background-color: #18181c;
            color: #f4f4f5;
        }
        label {
            color: #f4f4f5;
        }
        .keys-frame {
            border: 1px solid #363642;
            border-radius: 8px;
            font-weight: bold;
            background-color: #212128;
            color: #f4f4f5;
        }
        .keys-frame > border {
            border: 1px solid #363642;
        }
        .key-card {
            background-color: #282832;
            border-radius: 8px;
            border: 2px solid #3c3c4a;
            transition: all 150ms ease;
        }
        .key-card-active {
            border-color: #a29bfe;
            background-color: #342e52;
            box-shadow: 0 0 8px rgba(162, 155, 254, 0.4);
        }
        .emoji-display {
            font-size: 24px;
            padding: 2px;
            border-radius: 6px;
            border: 1px solid #4a4a5a;
            background-color: #1a1a22;
            color: #ffffff;
        }
        .test-btn {
            font-size: 11px;
            padding: 3px 6px;
            border-radius: 5px;
            background-color: #363644;
            color: #f4f4f5;
            border: 1px solid #4c4c5e;
        }
        .test-btn:hover {
            background-color: #48485c;
            border-color: #a29bfe;
        }
        .palette-frame {
            border: 1px solid #363642;
            border-radius: 8px;
            font-weight: bold;
            background-color: #212128;
            color: #f4f4f5;
        }
        .palette-notebook {
            background-color: #1f1f26;
        }
        .palette-notebook tab {
            padding: 4px 8px;
            font-weight: bold;
            font-size: 12px;
            background-color: #2a2a36;
            color: #d4d4d8;
        }
        .palette-notebook tab:checked {
            background-color: #383848;
            color: #ffffff;
            border-bottom: 2px solid #a29bfe;
        }
        .palette-emoji-btn {
            font-size: 18px;
            padding: 0;
            margin: 0;
            border-radius: 6px;
            background-color: #282834;
            border: 1px solid #3c3c4a;
            color: #ffffff;
        }
        .palette-emoji-btn:hover {
            background-color: #453c66;
            border-color: #a29bfe;
        }
        .key5-card {
            background-color: #22222b;
            border: 1px solid #383846;
            border-radius: 8px;
            color: #f4f4f5;
        }
        .test-btn-wide {
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 6px;
            background-color: #363644;
            color: #f4f4f5;
            border: 1px solid #4c4c5e;
        }
        .test-btn-wide:hover {
            background-color: #48485c;
            border-color: #a29bfe;
        }
        .save-btn {
            background-image: linear-gradient(to bottom, #7d6dfa, #5b4bc9);
            color: white;
            font-weight: bold;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #8e80ff;
        }
        .save-btn:hover {
            background-image: linear-gradient(to bottom, #8e80ff, #6c5ce7);
        }
        .reset-btn {
            font-size: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: #2a2a36;
            color: #e4e4e7;
            border: 1px solid #3f3f50;
        }
        .reset-btn:hover {
            background-color: #383848;
        }
        """
    else:
        return b"""
        window {
            background-color: #f8f9fa;
            color: #18181b;
        }
        label {
            color: #18181b;
        }
        .keys-frame {
            border: 1px solid #dcdce6;
            border-radius: 8px;
            font-weight: bold;
            background-color: #ffffff;
            color: #18181b;
        }
        .key-card {
            background-color: #fcfcfd;
            border-radius: 8px;
            border: 2px solid #e2e2ec;
            transition: all 150ms ease;
        }
        .key-card-active {
            border-color: #6c5ce7;
            background-color: #f7f4ff;
            box-shadow: 0 0 6px rgba(108, 92, 231, 0.3);
        }
        .emoji-display {
            font-size: 24px;
            padding: 2px;
            border-radius: 6px;
            border: 1px solid #ccc;
            background-color: #ffffff;
            color: #000000;
        }
        .test-btn {
            font-size: 11px;
            padding: 3px 6px;
            border-radius: 5px;
            background-color: #f1f3f6;
            color: #24292f;
            border: 1px solid #d0d7de;
        }
        .test-btn:hover {
            background-color: #e4e7eb;
            border-color: #6c5ce7;
        }
        .palette-frame {
            border: 1px solid #dcdce6;
            border-radius: 8px;
            font-weight: bold;
            background-color: #ffffff;
            color: #18181b;
        }
        .palette-notebook tab {
            padding: 4px 8px;
            font-weight: bold;
            font-size: 12px;
            background-color: #f1f3f6;
            color: #24292f;
        }
        .palette-notebook tab:checked {
            background-color: #ffffff;
            color: #6c5ce7;
            border-bottom: 2px solid #6c5ce7;
        }
        .palette-emoji-btn {
            font-size: 18px;
            padding: 0;
            margin: 0;
            border-radius: 6px;
            background-color: #ffffff;
            border: 1px solid #e0e0e8;
        }
        .palette-emoji-btn:hover {
            background-color: #f0edff;
            border-color: #6c5ce7;
        }
        .key5-card {
            background-color: #f1f3f6;
            border: 1px solid #d0d7de;
            border-radius: 8px;
            color: #18181b;
        }
        .test-btn-wide {
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 6px;
            background-color: #e4e7eb;
            color: #24292f;
            border: 1px solid #d0d7de;
        }
        .save-btn {
            background-image: linear-gradient(to bottom, #6c5ce7, #5344c7);
            color: white;
            font-weight: bold;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
        }
        .save-btn:hover {
            background-image: linear-gradient(to bottom, #7d6dfa, #6c5ce7);
        }
        .reset-btn {
            font-size: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: #f1f3f6;
            color: #24292f;
            border: 1px solid #d0d7de;
        }
        """

def get_picker_css(is_dark: bool) -> bytes:
    if is_dark:
        return b"""
        window {
            background-color: #1c1c22;
            color: #f4f4f5;
            border: 1px solid #363644;
            border-radius: 12px;
        }
        label {
            color: #f4f4f5;
        }
        entry {
            background-color: #282834;
            color: #f4f4f5;
            border: 1px solid #444456;
            border-radius: 6px;
            padding: 4px 8px;
        }
        entry:focus {
            border-color: #a29bfe;
        }
        .picker-close-btn {
            font-size: 13px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            background-color: #2a2a36;
            border: 1px solid #444456;
            color: #d4d4d8;
        }
        .picker-close-btn:hover {
            background-color: #4a2228;
            color: #ff858d;
            border-color: #ff858d;
        }
        .picker-notebook {
            background-color: #1e1e26;
        }
        .picker-notebook tab {
            padding: 4px 10px;
            font-size: 16px;
            background-color: #282834;
            color: #a1a1aa;
        }
        .picker-notebook tab:checked {
            background-color: #383848;
            color: #ffffff;
            border-bottom: 2px solid #a29bfe;
        }
        .picker-emoji-btn {
            font-size: 20px;
            padding: 0;
            margin: 0;
            border-radius: 6px;
            background-color: #282834;
            border: 1px solid #3c3c4a;
            color: #ffffff;
        }
        .picker-emoji-btn:hover {
            background-color: #453c66;
            border-color: #a29bfe;
        }
        """
    else:
        return b"""
        window {
            background-color: #f8f9fa;
            color: #18181b;
            border-radius: 12px;
        }
        label {
            color: #18181b;
        }
        entry {
            background-color: #ffffff;
            color: #18181b;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 4px 8px;
        }
        .picker-close-btn {
            font-size: 13px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            background-color: #f1f3f6;
            border: 1px solid #d0d7de;
            color: #24292f;
        }
        .picker-close-btn:hover {
            background-color: #ffeef0;
            color: #cf222e;
            border-color: #cf222e;
        }
        .picker-notebook tab {
            padding: 4px 10px;
            font-size: 16px;
            background-color: #f1f3f6;
        }
        .picker-notebook tab:checked {
            background-color: #ffffff;
            border-bottom: 2px solid #6c5ce7;
        }
        .picker-emoji-btn {
            font-size: 20px;
            padding: 0;
            margin: 0;
            border-radius: 6px;
            background-color: #ffffff;
            border: 1px solid #e1e4e8;
        }
        .picker-emoji-btn:hover {
            background-color: #f0edff;
            border-color: #6c5ce7;
        }
        """
