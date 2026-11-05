#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Instalador de LogiPop Emoji Studio
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      😃 Instalación de LogiPop Emoji Studio"
echo "=========================================================="
echo ""

# 1. Permisos de ejecución
chmod +x "$SCRIPT_DIR/emoji_manager.py" "$SCRIPT_DIR/send_emoji.py"
echo "✔ Permisos asignados a los scripts de Emoji Studio."

# 2. Instalar lanzador de escritorio .desktop
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat << EOF > "$APP_DIR/logipop-emojis.desktop"
[Desktop Entry]
Type=Application
Name=LogiPop Emoji Studio
Comment=Personalizador de teclas de emojis para Logitech POP Keys
Exec=python3 $SCRIPT_DIR/emoji_manager.py
Icon=$SCRIPT_DIR/logipop.svg
Terminal=false
Categories=Utility;Settings;
StartupNotify=true
EOF
chmod +x "$APP_DIR/logipop-emojis.desktop"
echo "✔ Acceso directo 'LogiPop Emoji Studio' instalado en el menú de aplicaciones."

# 3. Aplicar configuración inicial y reglas en Solaar
echo "⚙️ Configurando reglas de teclado en Solaar..."
python3 "$SCRIPT_DIR/emoji_manager.py" --apply || true

echo ""
echo "=========================================================="
echo "🎉 ¡LogiPop Emoji Studio instalado con éxito!"
echo "Puedes abrir la aplicación desde el menú de aplicaciones"
echo "o ejecutando: python3 $SCRIPT_DIR/emoji_manager.py"
echo "=========================================================="
