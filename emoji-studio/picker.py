#!/usr/bin/env python3
"""
picker.py - Selector Mini Flotante de Emojis para Logitech POP Keys
Muestra un panel compacto organizado por categorías. Al hacer clic en un emoji,
la ventana se cierra y pega automáticamente el emoji en la aplicación activa.
"""

import os
import sys
import socket

# Exclusivo Linux
if not sys.platform.startswith("linux"):
    sys.exit(0)

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, Pango

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_FILE = os.path.join(SCRIPT_DIR, "logipop.svg")

# Importar catálogo común y gestor de temas
from catalog import EMOJI_CATEGORIES
from theme import is_dark_mode, get_picker_css, setup_theme_listener

def get_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime_dir, f"logipop_emoji_{os.getuid()}.sock")

def send_paste_to_daemon(emoji_char: str):
    """Envía la orden al demonio para pegar el emoji seleccionado."""
    sock_path = get_socket_path()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_path)
        s.sendall(f"paste:{emoji_char}".encode("utf-8"))
        s.close()
    except Exception:
        pass

class MiniEmojiPicker(Gtk.Window):
    def __init__(self):
        super().__init__(title="LogiPop Emoji Picker")
        self.set_default_size(460, 390)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        if os.path.exists(ICON_FILE):
            try:
                self.set_icon_from_file(ICON_FILE)
            except Exception:
                pass

        # Proveedor de CSS dinámico para modo claro / oscuro
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.build_ui()

        # Escuchar cambios en el tema del sistema y aplicar el estilo inicial
        self.theme_listener = setup_theme_listener(self.on_theme_changed)
        self.apply_theme(is_dark_mode())

        # Atajo Esc para cerrar sin pegar
        self.connect("key-press-event", self.on_key_pressed)

    def update_header_colors(self, is_dark: bool):
        logi_color = "#A29BFE" if is_dark else "#6C5CE7"
        if hasattr(self, "title_lbl"):
            self.title_lbl.set_markup(
                f"<span font_desc='Ubuntu, Cantarell, Sans Bold 13' color='{logi_color}'>logi</span>"
                f"<span font_desc='Ubuntu, Cantarell, Sans Heavy 12' background='#FFD200' color='#18181B'> POP </span>"
            )

    def apply_theme(self, is_dark: bool):
        css = get_picker_css(is_dark)
        self.css_provider.load_from_data(css)
        self.update_header_colors(is_dark)

    def on_theme_changed(self, is_dark: bool):
        self.apply_theme(is_dark)

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_border_width(10)
        self.add(main_box)

        # 1. Barra de Encabezado y Búsqueda
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.title_lbl = Gtk.Label()
        self.update_header_colors(is_dark_mode())
        top_box.pack_start(self.title_lbl, False, False, 0)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Buscar emoji... (Esc para salir)")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        top_box.pack_start(self.search_entry, True, True, 0)

        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("picker-close-btn")
        close_btn.set_tooltip_text("Cerrar (Esc)")
        close_btn.connect("clicked", lambda w: self.close_without_paste())
        top_box.pack_start(close_btn, False, False, 0)

        main_box.pack_start(top_box, False, False, 0)

        # 2. Pila para alternar entre Categorías y Resultados de Búsqueda
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(100)
        main_box.pack_start(self.stack, True, True, 0)

        # A. Vista de Categorías en Pestañas (Notebook)
        self.notebook = Gtk.Notebook()
        self.notebook.get_style_context().add_class("picker-notebook")
        self.notebook.set_scrollable(True)

        for cat_name, emoji_list in EMOJI_CATEGORIES.items():
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_overlay_scrolling(True)

            grid = Gtk.Grid()
            grid.set_column_spacing(4)
            grid.set_row_spacing(4)
            grid.set_halign(Gtk.Align.CENTER)
            grid.set_valign(Gtk.Align.START)
            grid.set_border_width(6)

            cols = 9
            for i, em in enumerate(emoji_list):
                btn = Gtk.Button(label=em)
                btn.set_size_request(40, 40)
                btn.get_style_context().add_class("picker-emoji-btn")
                btn.connect("clicked", self.on_emoji_clicked, em)
                col = i % cols
                row = i // cols
                grid.attach(btn, col, row, 1, 1)

            scrolled.add(grid)
            tab_lbl = Gtk.Label(label=cat_name.split()[0])  # Solo el icono en la pestaña para ahorrar espacio
            tab_lbl.set_tooltip_text(cat_name)
            self.notebook.append_page(scrolled, tab_lbl)

        self.stack.add_named(self.notebook, "categories")

        # B. Vista de Búsqueda Rápida
        self.search_scrolled = Gtk.ScrolledWindow()
        self.search_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.search_grid = Gtk.Grid()
        self.search_grid.set_column_spacing(4)
        self.search_grid.set_row_spacing(4)
        self.search_grid.set_halign(Gtk.Align.CENTER)
        self.search_grid.set_valign(Gtk.Align.START)
        self.search_grid.set_border_width(6)
        self.search_scrolled.add(self.search_grid)

        self.stack.add_named(self.search_scrolled, "search")
        self.stack.set_visible_child_name("categories")

    def on_emoji_clicked(self, widget, emoji_char):
        """Al seleccionar un emoji, cierra la ventana y lo pega automáticamente."""
        # 1. Enviar orden de pegado al demonio
        send_paste_to_daemon(emoji_char)

        # 2. Cerrar la ventana inmediatamente para devolver el foco a la ventana anterior
        self.destroy()
        Gtk.main_quit()

    def on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            self.stack.set_visible_child_name("categories")
            return

        # Limpiar resultados anteriores
        for child in self.search_grid.get_children():
            self.search_grid.remove(child)

        # Buscar emojis que coincidan
        matches = []
        for cat, emojis in EMOJI_CATEGORIES.items():
            for em in emojis:
                if query in em.lower() or query in cat.lower():
                    matches.append(em)

        cols = 9
        for i, em in enumerate(matches[:81]):  # Limitar a máx 81 resultados
            btn = Gtk.Button(label=em)
            btn.set_size_request(40, 40)
            btn.get_style_context().add_class("picker-emoji-btn")
            btn.connect("clicked", self.on_emoji_clicked, em)
            col = i % cols
            row = i // cols
            self.search_grid.attach(btn, col, row, 1, 1)

        self.search_grid.show_all()
        self.stack.set_visible_child_name("search")

    def on_key_pressed(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_without_paste()
            return True
        return False

    def close_without_paste(self):
        self.destroy()
        Gtk.main_quit()



def main():
    app = MiniEmojiPicker()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
