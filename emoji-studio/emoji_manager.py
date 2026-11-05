#!/usr/bin/env python3
"""
emoji_manager.py - Gestor Gráfico para las Teclas de Emojis de Logitech POP Keys
Interfaz gráfica nativa en GTK3 con catálogo completo de emojis de Unicode
y nuevo logotipo oficial LogiPop vectorizado.
"""

import os
import sys

# Verificación de plataforma: LogiPop Emoji Studio es exclusivo para Linux
if not sys.platform.startswith("linux"):
    print("❌ Error: LogiPop Emoji Studio está diseñado exclusivamente para distribuciones Linux.")
    print("En Windows y macOS, los emojis se configuran con la suite oficial 'Logi Options+' de Logitech.")
    sys.exit(1)

import json
import subprocess
import yaml

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango, GLib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "emojis.json")
ICON_FILE = os.path.join(SCRIPT_DIR, "logipop.svg")
SOLAAR_CONFIG_DIR = os.path.expanduser("~/.config/solaar")
SOLAAR_CONFIG_FILE = os.path.join(SOLAAR_CONFIG_DIR, "config.yaml")
SOLAAR_RULES_FILE = os.path.join(SOLAAR_CONFIG_DIR, "rules.yaml")

DEFAULT_EMOJIS = {
    "1": "😍",
    "2": "😂",
    "3": "😊",
    "4": "🔥"
}

# Catálogo exhaustivo de Emojis de Unicode organizados por categorías completas
EMOJI_CATEGORIES = {
    "😀 Caras": [
        "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
        "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "😚", "😙",
        "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
        "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥",
        "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮",
        "🤧", "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳", "🥸", "😎",
        "🤓", "🧐", "😕", "😟", "🙁", "😮", "😯", "😲", "😳", "🥺",
        "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣",
        "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈",
        "👿", "💀", "☠️", "💩", "🤡", "👹", "👺", "👻", "👽", "🤖"
    ],
    "👍 Personas": [
        "👋", "🤚", "🖐️", "✋", "🖖", "🫱", "🫲", "🫳", "🫴", "👌",
        "🤌", "🤏", "✌️", "🤞", "🫰", "🤟", "🤘", "🤙", "👈", "👉",
        "👆", "🖕", "👇", "☝️", "🫵", "👍", "👎", "✊", "👊", "🤛",
        "🤜", "👏", "🙌", "🫶", "👐", "🤲", "🤝", "🙏", "✍️", "💅",
        "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻", "👃", "🧠",
        "🫀", "🫁", "🦷", "🦴", "👀", "👁️", "👅", "👄", "🫦", "👶",
        "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👩", "🧓", "👴",
        "👵", "🙍", "🙎", "🙅", "🙆", "💁", "🙋", "🧏", "🙇", "🤦",
        "🤷", "👮", "🕵️", "💂", "🥷", "👷", "🤴", "👸", "👳", "👲"
    ],
    "🐶 Animales": [
        "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯",
        "🦁", "🐮", "🐷", "🐽", "🐸", "🐵", "🙈", "🙉", "🙊", "🐒",
        "🐔", "🐧", "🐦", "🐤", "🐣", "🐥", "🦆", "🦅", "🦉", "🦇",
        "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋", "🐌", "🐞", "🐜",
        "🪰", "🪲", "🪳", "🦟", "🦗", "🕷️", "🕸️", "🦂", "🐢", "🐍",
        "🦎", "🦖", "🦕", "🐙", "🦑", "🦐", "🦞", "🦀", "🐡", "🐠",
        "🐟", "🐬", "🐳", "🐋", "🦈", "🐊", "🐆", "🐅", "🐃", "🐂",
        "🐄", "🦌", "🐪", "🐫", "🦙", "🦒", "🐘", "🦏", "🦛", "🐁",
        "🌲", "🌳", "🌴", "🌵", "🌾", "🌿", "☘️", "🍀", "🍁", "🍂"
    ],
    "🍕 Comida": [
        "🍇", "🍈", "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍏",
        "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🍅", "🫒", "🥥", "🥑",
        "🍆", "🥔", "🥕", "🌽", "🌶️", "🫑", "🥒", "🥬", "🥦", "🧄",
        "🧅", "🍄", "🥜", "🌰", "🍞", "🥐", "🥖", "🫓", "🥨", "🥯",
        "🥞", "🧇", "🧀", "🍖", "🍗", "🥩", "🥓", "🍔", "🍟", "🍕",
        "🌭", "🥪", "🌮", "🌯", "🫔", "🥙", "🧆", "🥚", "🍳", "🥘",
        "🍲", "🫕", "🥣", "🥗", "🍿", "🧈", "🧂", "🥫", "🍱", "🍘",
        "🍙", "🍚", "🍛", "🍜", "🍝", "🍠", "🍢", "🍣", "🍤", "🍥",
        "🍦", "🍧", "🍨", "🍩", "🍪", "🎂", "🍰", "🧁", "🥧", "🍫",
        "🍬", "🍭", "🍮", "🍯", "🍼", "🥛", "☕", "🫖", "🍵", "🍺"
    ],
    "⚽ Deportes": [
        "⚽", "⚾", "🥎", "🏀", "🏐", "🏈", "🏉", "🎾", "🥏", "🎳",
        "🏏", "🏑", "🏒", "🥍", "🏓", "🏸", "🥊", "🥋", "🥅", "⛳",
        "⛸️", "🎣", "🤿", "🎽", "🎿", "🛷", "🥌", "🎯", "🪀", "🪁",
        "🎱", "🔮", "🪄", "🎮", "🕹️", "🎰", "🎲", "🧩", "🧸", "🪅",
        "🪆", "🃏", "🀄", "🎭", "🎨", "🧵", "🪡", "🧶", "🎤", "🎧",
        "📻", "🎷", "🪗", "🎸", "🎹", "🎺", "🎻", "🪕", "🥁", "🎬",
        "🏹", "🛹", "🛼", "🏆", "🥇", "🥈", "🥉", "🏅", "🎖️", "🎫"
    ],
    "✈️ Viajes": [
        "🚗", "🚕", "🚙", "🚌", "🚎", "🏎️", "🚓", "🚑", "🚒", "🚐",
        "🛻", "🚚", "🚛", "🚜", "🏍️", "🛵", "🚲", "🛴", "🚨", "🚔",
        "🚍", "🚘", "🚖", "🚡", "🚠", "🚟", "🚃", "🚋", "🚞", "🚝",
        "🚄", "🚅", "🚈", "🚂", "🚆", "🚇", "🚊", "🚉", "✈️", "🛫",
        "🛬", "🛩️", "💺", "🛰️", "🚀", "🛸", "🚁", "🛶", "⛵", "🚤",
        "🛥️", "🛳️", "⛴️", "🚢", "⚓", "🛟", "⛽", "🚧", "🚦", "🚥",
        "🗺️", "🗿", "🗽", "🗼", "🏰", "🏯", "🏟️", "🎡", "🎢", "🎠",
        "⛱️", "🏖️", "🏝️", "🏜️", "🌋", "⛰️", "🏔️", "🏕️", "⛺", "🏠"
    ],
    "💡 Objetos": [
        "⌚", "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "💾", "💿",
        "📀", "📷", "📸", "📹", "🎥", "📽️", "🎞️", "📞", "☎️", "📟",
        "📺", "📻", "🎙️", "🎚️", "🎛️", "⏱️", "⏲️", "⏰", "🕰️", "⌛",
        "⏳", "📡", "🔋", "🪫", "🔌", "💡", "🔦", "🕯️", "🧯", "🗑️",
        "💸", "💵", "💴", "💶", "💷", "🪙", "💰", "💳", "💎", "⚖️",
        "🪜", "🧰", "🪛", "🔧", "🔨", "⚒️", "🛠️", "⛏️", "🪚", "🔩",
        "⚙️", "⛓️", "🧲", "💣", "🧨", "🪓", "🔪", "🗡️", "⚔️", "🛡️",
        "💊", "💉", "🩸", "🩹", "🩺", "🔑", "🗝️", "🚪", "📦", "📫",
        "📄", "📑", "🧾", "📊", "📈", "📉", "📅", "📆", "📁", "📂",
        "📚", "📖", "🔖", "🔗", "📎", "📌", "📍", "✂️", "📝", "✏️"
    ],
    "💖 Símbolos": [
        "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
        "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "⭐",
        "🌟", "💫", "✨", "💥", "💢", "💬", "💭", "💤", "💯", "🔥",
        "⚡", "🌈", "☀️", "🌙", "☁️", "🌧️", "❄️", "☃️", "💧", "🌊",
        "✅", "❌", "⚠️", "❓", "❗", "‼️", "⁉️", "⛔", "🚫", "🛑",
        "♻️", "🌐", "🔔", "🔕", "📢", "📣", "🔒", "🔓", "🔏", "🔐",
        "➡️", "⬅️", "⬆️", "⬇️", "↗️", "↘️", "↙️", "↖️", "↕️", "↔️",
        "🔄", "🔁", "🔂", "▶️", "⏸️", "⏹️", "⏺️", "⏭️", "⏮️", "⏩",
        "🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚫", "⚪", "🟤", "🔺",
        "🔻", "🔸", "🔹", "🔶", "🔷", "🔳", "🔲", "🏁", "🚩", "🎌"
    ]
}

class EmojiManagerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="LogiPop Emoji Studio")
        self.set_default_size(630, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)

        # Cargar icono de ventana desde logipop.svg
        if os.path.exists(ICON_FILE):
            try:
                self.set_icon_from_file(ICON_FILE)
            except Exception:
                pass

        self.emojis = self.load_config()
        self.selected_key_idx = "1"
        self.entries = {}
        self.cards = {}

        self.apply_css()
        self.build_ui()

    def build_ui(self):
        # Contenedor con Scroll para garantizar que nunca se corte la ventana
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_overlay_scrolling(True)
        self.add(scrolled)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_border_width(14)
        scrolled.add(main_box)

        # ======================================================================
        # 1. Encabezado con el Nuevo Logotipo Oficial LogiPop
        # ======================================================================
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        header_box.set_halign(Gtk.Align.CENTER)
        header_box.set_margin_bottom(2)

        if os.path.exists(ICON_FILE):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(ICON_FILE, 48, 48, True)
                logo_img = Gtk.Image.new_from_pixbuf(pixbuf)
                header_box.pack_start(logo_img, False, False, 0)
            except Exception:
                pass

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        logo_label = Gtk.Label()
        logo_label.set_markup(
            "<span font_desc='Ubuntu, Cantarell, Sans Bold 20' color='#1E1E24'>logi</span>"
            "<span font_desc='Ubuntu, Cantarell, Sans Heavy 18' background='#FFD200' color='#18181B'> POP </span>"
            "<span font_desc='Ubuntu, Cantarell, Sans Bold 11' color='#6C5CE7'> EMOJI STUDIO</span>"
        )
        logo_label.set_xalign(0)

        subtitle_label = Gtk.Label()
        subtitle_label.set_markup("<span size='small' color='#666'>Configurador de teclas de emojis para Logitech POP Keys (Linux)</span>")
        subtitle_label.set_xalign(0)

        title_vbox.pack_start(logo_label, False, False, 0)
        title_vbox.pack_start(subtitle_label, False, False, 0)
        header_box.pack_start(title_vbox, False, False, 0)

        main_box.pack_start(header_box, False, False, 0)

        # ======================================================================
        # 2. Las 4 Teclas Físicas de Emojis (Organizadas Horizontalmente)
        # ======================================================================
        keys_frame = Gtk.Frame(label=" 4 Teclas Físicas de Emojis (Borde Derecho del Teclado) ")
        keys_frame.get_style_context().add_class("keys-frame")

        keys_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        keys_box.set_border_width(8)
        keys_box.set_homogeneous(True)

        key_meta = [
            ("1", "Tecla 1", "Superior", self.emojis.get("1", "😍")),
            ("2", "Tecla 2", "Media 1", self.emojis.get("2", "😂")),
            ("3", "Tecla 3", "Media 2", self.emojis.get("3", "😊")),
            ("4", "Tecla 4", "Inferior", self.emojis.get("4", "🔥")),
        ]

        for idx, title, subtitle, val in key_meta:
            card = Gtk.EventBox()
            card.get_style_context().add_class("key-card")
            if idx == self.selected_key_idx:
                card.get_style_context().add_class("key-card-active")

            c_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            c_box.set_border_width(6)

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
            c_box.pack_start(entry, False, False, 2)
            c_box.pack_start(test_btn, False, False, 2)

            card.add(c_box)
            card.connect("button-press-event", self.on_card_clicked, idx)

            self.entries[idx] = entry
            self.cards[idx] = card
            keys_box.pack_start(card, True, True, 0)

        keys_frame.add(keys_box)
        main_box.pack_start(keys_frame, False, False, 0)

        # ======================================================================
        # 3. Catálogo Completo de Emojis en Matriz Scrollable (10 Columnas)
        # ======================================================================
        palette_frame = Gtk.Frame(label=" Catálogo Completo de Emojis (Haz clic en un emoji para asignarlo a la tecla activa) ")
        palette_frame.get_style_context().add_class("palette-frame")

        notebook = Gtk.Notebook()
        notebook.get_style_context().add_class("palette-notebook")
        notebook.set_scrollable(True)

        for cat_name, emoji_list in EMOJI_CATEGORIES.items():
            # Contenedor con scroll interno para cada categoría
            cat_scroll = Gtk.ScrolledWindow()
            cat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            cat_scroll.set_min_content_height(180)
            cat_scroll.set_max_content_height(190)

            grid = Gtk.Grid()
            grid.set_column_spacing(4)
            grid.set_row_spacing(4)
            grid.set_halign(Gtk.Align.CENTER)
            grid.set_valign(Gtk.Align.START)
            grid.set_border_width(8)

            cols = 10
            for i, em in enumerate(emoji_list):
                btn = Gtk.Button(label=em)
                btn.set_size_request(36, 36)
                btn.get_style_context().add_class("palette-emoji-btn")
                btn.set_tooltip_text(f"Asignar {em} a la tecla activa")
                btn.connect("clicked", self.on_quick_emoji_selected, em)

                col = i % cols
                row = i // cols
                grid.attach(btn, col, row, 1, 1)

            cat_scroll.add(grid)
            tab_lbl = Gtk.Label(label=cat_name)
            notebook.append_page(cat_scroll, tab_lbl)

        palette_frame.add(notebook)
        main_box.pack_start(palette_frame, False, False, 0)

        # ======================================================================
        # 4. Tecla 5: Selector Completo de Emojis del Sistema
        # ======================================================================
        p5_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        p5_box.get_style_context().add_class("key5-card")
        p5_box.set_border_width(8)

        p5_icon = Gtk.Label()
        p5_icon.set_markup("<span size='x-large'>🌐</span>")

        p5_info = Gtk.Label()
        p5_info.set_markup(
            "<b>Tecla 5: Selector Global de Emojis</b>  "
            "<span size='small' color='#555'>(Abre el panel nativo de GNOME: Super + .)</span>"
        )
        p5_info.set_xalign(0)

        p5_test = Gtk.Button(label="🧪 Probar Selector")
        p5_test.get_style_context().add_class("test-btn-wide")
        p5_test.connect("clicked", self.on_test_key_clicked, "5")

        p5_box.pack_start(p5_icon, False, False, 0)
        p5_box.pack_start(p5_info, True, True, 0)
        p5_box.pack_start(p5_test, False, False, 0)
        main_box.pack_start(p5_box, False, False, 0)

        # ======================================================================
        # 5. Barra Inferior de Acciones
        # ======================================================================
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_top(2)

        reset_btn = Gtk.Button(label="↺ Valores por Defecto")
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
        send_script = os.path.join(SCRIPT_DIR, "send_emoji.sh")
        subprocess.Popen([send_script, str(idx)])

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

        # 2. Notificar inmediatamente al demonio para pre-calentar el portapapeles (< 2ms)
        send_script = os.path.join(SCRIPT_DIR, "send_emoji.sh")
        try:
            subprocess.run([send_script, "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        # 3. Configurar Solaar divert-keys y rules.yaml (solo reinicia si es primera vez)
        solaar_ok, solaar_msg = self.apply_solaar_integration()

        # 4. Mostrar confirmación
        summary_text = (
            f"<b>¡Configuración guardada exitosamente!</b>\n\n"
            f"• Tecla 1: {new_config['1']}\n"
            f"• Tecla 2: {new_config['2']}\n"
            f"• Tecla 3: {new_config['3']}\n"
            f"• Tecla 4: {new_config['4']}\n"
            f"• Tecla 5: Selector Global (Super + .)\n\n"
            f"{solaar_msg}"
        )
        self.show_message(Gtk.MessageType.INFO, "LogiPop Emojis Aplicados", summary_text)

    def apply_solaar_integration(self):
        os.makedirs(SOLAAR_CONFIG_DIR, exist_ok=True)
        send_script = os.path.join(SCRIPT_DIR, "send_emoji.sh")

        # Verificar si las reglas ya están instaladas
        rules_already_installed = False
        if os.path.exists(SOLAAR_RULES_FILE):
            try:
                with open(SOLAAR_RULES_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                    if send_script in content or "send_emoji" in content:
                        rules_already_installed = True
            except Exception:
                pass

        # Si ya están vinculadas, NO reiniciar Solaar para evitar demoras de conexión de hardware
        if rules_already_installed:
            return True, "⚡ Aplicado instantáneamente. El teclado mantiene su conexión activa sin demoras."

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
            [{"Key": ["Emoji Smiley Heart Eyes", "pressed"]}, {"Execute": [send_script, "1"]}],
            [{"Key": ["Emoji Crying Face", "pressed"]}, {"Execute": [send_script, "2"]}],
            [{"Key": ["Emoji Smiley", "pressed"]}, {"Execute": [send_script, "3"]}],
            [{"Key": ["Emoji Smilie With Tears", "pressed"]}, {"Execute": [send_script, "4"]}],
            [{"Key": ["Emoji", "pressed"]}, {"Execute": [send_script, "5"]}],
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
            background-color: #f8f9fa;
        }
        .keys-frame {
            border: 1px solid #dcdce6;
            border-radius: 8px;
            font-weight: bold;
            background-color: #ffffff;
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
        }
        .test-btn {
            font-size: 11px;
            padding: 3px 6px;
            border-radius: 5px;
        }
        .palette-frame {
            border: 1px solid #dcdce6;
            border-radius: 8px;
            font-weight: bold;
            background-color: #ffffff;
        }
        .palette-notebook tab {
            padding: 4px 8px;
            font-weight: bold;
            font-size: 12px;
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
        }
        .test-btn-wide {
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 6px;
        }
        .save-btn {
            background-image: linear-gradient(to bottom, #6c5ce7, #5344c7);
            color: white;
            font-weight: bold;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 6px;
        }
        .reset-btn {
            font-size: 12px;
            padding: 8px 12px;
            border-radius: 6px;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

def main():
    if "--apply" in sys.argv or "--setup" in sys.argv:
        app = EmojiManagerWindow()
        ok, msg = app.apply_solaar_integration()
        print(f"✔ Integración con Solaar: {msg}")
        app.destroy()
        return

    app = EmojiManagerWindow()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
