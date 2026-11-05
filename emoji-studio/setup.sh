#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Instalador de LogiPop Emoji Studio
# ==============================================================================

set -euo pipefail

# Verificación de plataforma
if [[ "${OSTYPE:-}" != "linux"* ]]; then
    echo "❌ Error: LogiPop Emoji Studio está diseñado exclusivamente para entornos Linux."
    echo "En Windows, los emojis se configuran a través del software oficial de Logitech (Logi Options+)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      😃 Instalación de LogiPop Emoji Studio"
echo "=========================================================="
echo ""

# 1. Permisos de ejecución
chmod +x "$SCRIPT_DIR/emoji_manager.py" "$SCRIPT_DIR/send_emoji.py" "$SCRIPT_DIR/send_emoji.sh" "$SCRIPT_DIR/daemon.py" "$SCRIPT_DIR/picker.py" "$SCRIPT_DIR/bin/wl-copy" "$SCRIPT_DIR/bin/wl-paste"
echo "✔ Permisos asignados a los scripts y binarios de Emoji Studio."

# 2. Instalar iconos en el tema del sistema (XDG Icon Theme) para menú, dock y ventana
ICON_THEME_DIR="$HOME/.local/share/icons/hicolor"
mkdir -p "$ICON_THEME_DIR/scalable/apps"
mkdir -p "$ICON_THEME_DIR/256x256/apps"
mkdir -p "$ICON_THEME_DIR/128x128/apps"
mkdir -p "$ICON_THEME_DIR/64x64/apps"
mkdir -p "$ICON_THEME_DIR/48x48/apps"

cp -f "$SCRIPT_DIR/logipop.svg" "$ICON_THEME_DIR/scalable/apps/logipop.svg"

python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

svg_path = '$SCRIPT_DIR/logipop.svg'
icon_base = '$ICON_THEME_DIR'
try:
    pb = GdkPixbuf.Pixbuf.new_from_file(svg_path)
    for sz in [256, 128, 64, 48]:
        scaled = pb.scale_simple(sz, sz, GdkPixbuf.InterpType.BILINEAR)
        scaled.savev(f'{icon_base}/{sz}x{sz}/apps/logipop.png', 'png', [], [])
except Exception:
    pass
"
gtk-update-icon-cache -f -t "$ICON_THEME_DIR" >/dev/null 2>&1 || true
echo "✔ Iconos oficiales 'logipop' instalados en el tema del sistema (SVG + PNG multi-resolución)."

# 3. Instalar lanzador de escritorio .desktop
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat << EOF > "$APP_DIR/logipop-emojis.desktop"
[Desktop Entry]
Type=Application
Name=LogiPop Emoji Studio
GenericName=Configurador de Emojis
Comment=Personalizador de teclas de emojis para Logitech POP Keys
Exec=python3 $SCRIPT_DIR/emoji_manager.py
Icon=logipop
Terminal=false
Categories=Utility;Settings;GTK;
StartupNotify=true
StartupWMClass=logipop-emojis
EOF
chmod +x "$APP_DIR/logipop-emojis.desktop"
update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
echo "✔ Acceso directo 'LogiPop Emoji Studio' instalado en el menú de aplicaciones y dock."

# 4. Configurar inicio automático del demonio en segundo plano
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat << EOF > "$AUTOSTART_DIR/logipop-daemon.desktop"
[Desktop Entry]
Type=Application
Name=LogiPop Emoji Daemon
Comment=Demonio de inyección ultrarrápida de emojis para Logitech POP Keys
Exec=python3 $SCRIPT_DIR/daemon.py
Terminal=false
Categories=Utility;
StartupNotify=false
EOF
echo "✔ Demonio de teclado virtual configurado para inicio automático en el arranque."

# 5. Iniciar o reiniciar el demonio en segundo plano
pkill -f "$SCRIPT_DIR/daemon.py" 2>/dev/null || true
sleep 0.3
nohup python3 "$SCRIPT_DIR/daemon.py" </dev/null &>/dev/null &
echo "✔ Demonio de inyección activo en segundo plano."

# 6. Aplicar configuración inicial y reglas en Solaar
echo "⚙️ Configurando reglas de teclado en Solaar..."
python3 "$SCRIPT_DIR/emoji_manager.py" --apply || true

echo ""
echo "=========================================================="
echo "🎉 ¡LogiPop Emoji Studio instalado con éxito!"
echo "Puedes abrir la aplicación desde el menú de aplicaciones"
echo "o ejecutando: python3 $SCRIPT_DIR/emoji_manager.py"
echo "=========================================================="
