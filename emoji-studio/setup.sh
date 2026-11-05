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
chmod +x "$SCRIPT_DIR/emoji_manager.py" "$SCRIPT_DIR/send_emoji.py" "$SCRIPT_DIR/send_emoji.sh" "$SCRIPT_DIR/daemon.py" "$SCRIPT_DIR/bin/wl-copy" "$SCRIPT_DIR/bin/wl-paste"
echo "✔ Permisos asignados a los scripts y binarios de Emoji Studio."

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

# 3. Configurar inicio automático del demonio en segundo plano
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

# 4. Iniciar el demonio en segundo plano
nohup python3 "$SCRIPT_DIR/daemon.py" </dev/null &>/dev/null &
echo "✔ Demonio de inyección activo en segundo plano."

# 5. Aplicar configuración inicial y reglas en Solaar
echo "⚙️ Configurando reglas de teclado en Solaar..."
python3 "$SCRIPT_DIR/emoji_manager.py" --apply || true

echo ""
echo "=========================================================="
echo "🎉 ¡LogiPop Emoji Studio instalado con éxito!"
echo "Puedes abrir la aplicación desde el menú de aplicaciones"
echo "o ejecutando: python3 $SCRIPT_DIR/emoji_manager.py"
echo "=========================================================="
