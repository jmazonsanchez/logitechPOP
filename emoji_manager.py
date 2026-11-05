#!/usr/bin/env python3
"""
emoji_manager.py - Gestor Gráfico para las Teclas de Emojis de Logitech POP Keys
Interfaz gráfica nativa en GTK3 para personalizar las 4 teclas de emojis y el selector general.
"""

import os
import sys
import json
import subprocess
import yaml

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GLib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "emojis.json")
SOLAAR_CONFIG_DIR = os.path.expanduser("~/.config/solaar")
SOLAAR_CONFIG_FILE = os.path.join(SOLAAR_CONFIG_DIR, "config.yaml")
SOLAAR_RULES_FILE = os.path.join(SOLAAR_CONFIG_DIR, "rules.yaml")

DEFAULT_EMOJIS = {
    "1": "😍",
    "2": "😂",
    "3": "😊",
    "4": "🔥"
}

PALETTES = {
    "😊 Expresiones": ["😍", "😂", "😊", "🔥", "😭", "🥳", "🤔", "😎", "🥰", "🤣", "🙄", "🥺", "😴", "😇", "🤯", "🤩"],
    "👍 Gestos": ["👍", "👏", "🙏", "✌️", "🤝", "👊", "💪", "👋", "🤞", "👌", "🤘", "🤙", "👈", "👉", "✍️", "🙌"],
    "✨ Símbolos": ["❤️", "✨", "💡", "🚀", "🎉", "💯", "☕", "⭐", "⚡", "💬", "🎯", "🏆", "💻", "📌", "🎨", "🔥"],
    "💼 Trabajo": ["✅", "❌", "⚠️", "❓", "❗", "⏳", "📅", "💼", "📊", "🔍", "📢", "🔔", "🎁", "🧠", "📝", "🔒"]
}

class EmojiManagerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="LogiPop Emoji Studio")
        self.set_default_size(560, 680)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(False)

        self.emojis = self.load_config()
        self.selected_key_idx = "1"
        self.entries = {}
        self.cards = {}

        self.apply_css()
        self.build_ui()

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        main_box.set_border_width(18)
        self.add(main_box)

        # 1. Encabezado
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_label = Gtk.Label()
        title_label.set_markup("<span size='xx-large' weight='bold'>⌨️ Logitech POP Emojis</span>")
        title_label.set_halign(Gtk.Align.CENTER)

        subtitle_label = Gtk.Label()
        subtitle_label.set_markup("<span color='#666'>Personaliza los 4 botones físicos de emojis y el selector general del POP Keys</span>")
        subtitle_label.set_halign(Gtk.Align.CENTER)

        header_box.pack_start(title_label, False, False, 0)
        header_box.pack_start(subtitle_label, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # 2. Contenedor de las 4 teclas físicas
        keys_frame = Gtk.Frame(label=" 4 Teclas Físicas de Emojis ")
        keys_frame.get_style_context().add_class("keys-frame")
        keys_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        keys_box.set_border_width(12)
        keys_box.set_homogeneous(True)

        key_meta = [
            ("1", "Tecla 1", "Superior (Heart Eyes)", self.emojis.get("1", "😍")),
            ("2", "Tecla 2", "Media 1 (Crying)", self.emojis.get("2", "😂")),
            ("3", "Tecla 3", "Media 2 (Smiley)", self.emojis.get("3", "😊")),
            ("4", "Tecla 4", "Inferior (Tears/Fire)", self.emojis.get("4", "🔥")),
        ]

        for idx, title, subtitle, val in key_meta:
            card = Gtk.EventBox()
            card.get_style_context().add_class("key-card")
            if idx == self.selected_key_idx:
                card.get_style_context().add_class("key-card-active")

            c_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            c_box.set_border_width(8)

            t_lbl = Gtk.Label()
            t_lbl.set_markup(f"<b>{title}</b>")

            sub_lbl = Gtk.Label()
            sub_lbl.set_markup(f"<span size='xx-small' color='#777'>{subtitle}</span>")

            entry = Gtk.Entry()
            entry.set_text(val)
            entry.set_max_length(4)
            entry.set_alignment(0.5)
            entry.get_style_context().add_class("emoji-display")
            entry.connect("focus-in-event", self.on_entry_focused, idx)
            entry.connect("changed", self.on_entry_changed, idx)

            test_btn = Gtk.Button(label="📋 Probar")
            test_btn.get_style_context().add_class("test-btn")
            test_btn.connect("clicked", self.on_test_key_clicked, idx)

            c_box.pack_start(t_lbl, False, False, 0)
            c_box.pack_start(sub_lbl, False, False, 0)
            c_box.pack_start(entry, False, False, 4)
            c_box.pack_start(test_btn, False, False, 0)

            card.add(c_box)
            card.connect("button-press-event", self.on_card_clicked, idx)

            self.entries[idx] = entry
            self.cards[idx] = card
            keys_box.pack_start(card, True, True, 0)

        keys_frame.add(keys_box)
        main_box.pack_start(keys_frame, False, False, 0)

        # 3. Paleta de selección rápida por categorías
        palette_frame = Gtk.Frame(label=" Paleta de Emojis Rápidos (Haz clic para asignar a la tecla activa) ")
        palette_frame.get_style_context().add_class("palette-frame")

        notebook = Gtk.Notebook()
        notebook.get_style_context().add_class("palette-notebook")

        for cat_name, emoji_list in PALETTES.items():
            flow = Gtk.FlowBox()
            flow.set_max_children_per_line(8)
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_halign(Gtk.Align.CENTER)
            flow.set_border_width(8)

            for em in emoji_list:
                btn = Gtk.Button(label=em)
                btn.get_style_context().add_class("palette-emoji-btn")
                btn.connect("clicked", self.on_quick_emoji_selected, em)
                flow.add(btn)

            tab_lbl = Gtk.Label(label=cat_name)
            notebook.append_page(flow, tab_lbl)

        palette_frame.add(notebook)
        main_box.pack_start(palette_frame, False, False, 0)

        # 4. Información Tecla 5 (Selector General)
        p5_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        p5_box.get_style_context().add_class("key5-card")
        p5_box.set_border_width(10)

        p5_icon = Gtk.Label()
        p5_icon.set_markup("<span size='xx-large'>🌐</span>")

        p5_info = Gtk.Label()
        p5_info.set_markup(
            "<b>Tecla 5: Selector Completo de Emojis (Panel Global)</b>\n"
            "<span size='small' color='#555'>Presiona el 5to botón de tu teclado para desplegar el selector nativo del sistema (Super + . / Ctrl + .)</span>"
        )
        p5_info.set_xalign(0)

        p5_test = Gtk.Button(label="🧪 Probar Selector")
        p5_test.get_style_context().add_class("test-btn-wide")
        p5_test.connect("clicked", self.on_test_key_clicked, "5")

        p5_box.pack_start(p5_icon, False, False, 0)
        p5_box.pack_start(p5_info, True, True, 0)
        p5_box.pack_start(p5_test, False, False, 0)
        main_box.pack_start(p5_box, False, False, 0)

        # 5. Barra Inferior de Acciones
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        reset_btn = Gtk.Button(label="↺ Restablecer Valores")
        reset_btn.get_style_context().add_class("reset-btn")
        reset_btn.connect("clicked", self.on_reset_clicked)

        save_btn = Gtk.Button(label="💾 Guardar y Aplicar al Teclado")
        save_btn.get_style_context().add_class("save-btn")
        save_btn.connect("clicked", self.on_save_clicked)

        btn_box.pack_start(reset_btn, False, False, 0)
        btn_box.pack_end(save_btn, True, True, 0)
        main_box.pack_end(btn_box, False, False, 0)

    def select_key(self, idx):
        self.selected_key_idx = idx
        for k, card in self.cards.items():
            if k == idx:
                card.get_style_context().add_class("key-card-active")
            else:
                card.get_style_context().remove_class("key-card-active")

    def on_card_clicked(self, widget, event, idx):
        self.select_key(idx)
        self.entries[idx].grab_focus()

    def on_entry_focused(self, widget, event, idx):
        self.select_key(idx)

    def on_entry_changed(self, entry, idx):
        self.emojis[idx] = entry.get_text()

    def on_quick_emoji_selected(self, widget, emoji_char):
        if self.selected_key_idx in self.entries:
            entry = self.entries[self.selected_key_idx]
            entry.set_text(emoji_char)
            self.emojis[self.selected_key_idx] = emoji_char

    def on_test_key_clicked(self, widget, idx):
        send_script = os.path.join(SCRIPT_DIR, "send_emoji.py")
        subprocess.Popen(["python3", send_script, str(idx)])

    def on_reset_clicked(self, widget):
        for idx, val in DEFAULT_EMOJIS.items():
            self.entries[idx].set_text(val)
            self.emojis[idx] = val

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    return {**DEFAULT_EMOJIS, **cfg}
            except Exception:
                pass
        return DEFAULT_EMOJIS.copy()

    def on_save_clicked(self, widget):
        # 1. Guardar emojis.json
        new_config = {k: self.entries[k].get_text() or DEFAULT_EMOJIS[k] for k in ["1", "2", "3", "4"]}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.show_message(Gtk.MessageType.ERROR, "Error al guardar", f"No se pudo guardar la configuración: {e}")
            return

        # 2. Configurar Solaar divert-keys y rules.yaml
        solaar_ok, solaar_msg = self.apply_solaar_integration()

        # 3. Mostrar confirmación
        summary_text = (
            f"<b>¡Configuración guardada exitosamente!</b>\n\n"
            f"• Tecla 1: {new_config['1']}\n"
            f"• Tecla 2: {new_config['2']}\n"
            f"• Tecla 3: {new_config['3']}\n"
            f"• Tecla 4: {new_config['4']}\n"
            f"• Tecla 5: Selector Completo (Super + .)\n\n"
            f"{solaar_msg}"
        )
        self.show_message(Gtk.MessageType.INFO, "LogiPop Emojis Aplicados", summary_text)

    def apply_solaar_integration(self):
        os.makedirs(SOLAAR_CONFIG_DIR, exist_ok=True)
        send_script = os.path.join(SCRIPT_DIR, "send_emoji.py")

        # A. Actualizar config.yaml para activar divert-keys en POP Keys
        try:
            if os.path.exists(SOLAAR_CONFIG_FILE):
                with open(SOLAAR_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("_NAME") == "Logi POP Keys":
                            dk = item.get("divert-keys", {})
                            for key_id in [260, 261, 262, 263, 264]:
                                dk[key_id] = 1
                            item["divert-keys"] = dk
                    with open(SOLAAR_CONFIG_FILE, "w", encoding="utf-8") as f:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return False, f"Advertencia al modificar Solaar config: {e}"

        # B. Actualizar rules.yaml preservando otras reglas existentes
        emoji_key_names = {
            "Emoji Smiley Heart Eyes",
            "Emoji Crying Face",
            "Emoji Smiley",
            "Emoji Smilie With Tears",
            "Emoji"
        }

        def is_emoji_rule(doc):
            if not isinstance(doc, list):
                return False
            for comp in doc:
                if isinstance(comp, dict):
                    if "Rule" in comp:
                        return is_emoji_rule(comp["Rule"])
                    if "Key" in comp:
                        k = comp["Key"]
                        if isinstance(k, list) and len(k) > 0 and k[0] in emoji_key_names:
                            return True
            return False

        existing_rules = []
        if os.path.exists(SOLAAR_RULES_FILE):
            try:
                with open(SOLAAR_RULES_FILE, "r", encoding="utf-8") as f:
                    for d in yaml.safe_load_all(f):
                        if d and not is_emoji_rule(d):
                            existing_rules.append(d)
            except Exception:
                existing_rules = []

        new_emoji_rules = [
            [{"Rule": [{"Key": ["Emoji Smiley Heart Eyes", "pressed"]}, {"Execute": ["python3", send_script, "1"]}]}],
            [{"Rule": [{"Key": ["Emoji Crying Face", "pressed"]}, {"Execute": ["python3", send_script, "2"]}]}],
            [{"Rule": [{"Key": ["Emoji Smiley", "pressed"]}, {"Execute": ["python3", send_script, "3"]}]}],
            [{"Rule": [{"Key": ["Emoji Smilie With Tears", "pressed"]}, {"Execute": ["python3", send_script, "4"]}]}],
            [{"Rule": [{"Key": ["Emoji", "pressed"]}, {"Execute": ["python3", send_script, "5"]}]}],
        ]

        all_rules = existing_rules + new_emoji_rules

        try:
            with open(SOLAAR_RULES_FILE, "w", encoding="utf-8") as f:
                f.write("%YAML 1.3\n# Reglas automáticas para Logitech POP (LogiPop Studio)\n")
                yaml.dump_all(all_rules, f, explicit_start=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            return False, f"Advertencia al escribir rules.yaml: {e}"

        # C. Reiniciar Solaar para aplicar cambios
        try:
            subprocess.run(["killall", "-q", "solaar"], stderr=subprocess.DEVNULL)
            subprocess.Popen(
                ["solaar", "--window=hide"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )
            return True, "Solaar se ha recargado en segundo plano con las nuevas reglas activadas."
        except Exception:
            return True, "Reglas guardadas. Si Solaar está abierto, reinícialo para aplicar cambios."

    def show_message(self, msg_type, title, text):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_markup(text)
        dialog.run()
        dialog.destroy()

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            background-color: #fafafa;
        }
        .keys-frame {
            border: 1px solid #d0d0d8;
            border-radius: 10px;
            font-weight: bold;
        }
        .key-card {
            background-color: #ffffff;
            border-radius: 8px;
            border: 2px solid #e2e2ea;
            transition: all 200ms ease;
        }
        .key-card-active {
            border-color: #6200ea;
            background-color: #f6f0ff;
            box-shadow: 0 0 8px rgba(98, 0, 234, 0.25);
        }
        .emoji-display {
            font-size: 26px;
            padding: 4px;
            border-radius: 8px;
            border: 1px solid #ccc;
            background-color: #fff;
        }
        .test-btn {
            font-size: 11px;
            padding: 4px 6px;
            border-radius: 6px;
        }
        .palette-frame {
            border: 1px solid #d0d0d8;
            border-radius: 10px;
            font-weight: bold;
        }
        .palette-notebook tab {
            padding: 6px 10px;
            font-weight: bold;
        }
        .palette-emoji-btn {
            font-size: 20px;
            padding: 4px 8px;
            margin: 2px;
            border-radius: 6px;
        }
        .key5-card {
            background-color: #f0f4f8;
            border: 1px solid #d0d8e2;
            border-radius: 8px;
        }
        .test-btn-wide {
            font-size: 12px;
            padding: 6px 12px;
            border-radius: 6px;
        }
        .save-btn {
            background-image: linear-gradient(to bottom, #6200ea, #4a00b0);
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 10px 16px;
            border-radius: 8px;
        }
        .reset-btn {
            font-size: 13px;
            padding: 10px 14px;
            border-radius: 8px;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

def main():
    app = EmojiManagerWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
