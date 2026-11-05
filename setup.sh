#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Maestro de Instalación y Configuración para LogiPop Sync
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      🚀 Configuración de Sincronización LogiPop"
echo "=========================================================="
echo ""

# 1. Permisos de ejecución
chmod +x "$SCRIPT_DIR/switch-host.sh" "$SCRIPT_DIR/configure-shortcuts.sh"
echo "✔ Permisos asignados a los scripts."

# 2. Comprobar Solaar
if ! command -v solaar >/dev/null 2>&1; then
    echo ""
    echo "⚠️ 'solaar' no está instalado en este equipo."
    echo "Por favor, abre una terminal e instala Solaar ejecutando:"
    echo "    sudo apt update && sudo apt install -y solaar"
    echo ""
    read -p "¿Deseas intentar instalarlo ahora con sudo? (s/N): " resp || resp="n"
    if [[ "$resp" =~ ^[sSyY]$ ]]; then
        sudo apt update && sudo apt install -y solaar
    else
        echo "Continuando sin instalar por ahora..."
    fi
else
    echo "✔ Solaar detectado: $(solaar --version 2>/dev/null || echo 'instalado')"
fi

# 3. Instalar reglas de Solaar
SOLAAR_CONFIG_DIR="$HOME/.config/solaar"
mkdir -p "$SOLAAR_CONFIG_DIR"

if [[ -f "$SCRIPT_DIR/rules.yaml" ]]; then
    if [[ -f "$SOLAAR_CONFIG_DIR/rules.yaml" ]]; then
        echo "ℹ Ya existe rules.yaml en $SOLAAR_CONFIG_DIR. Creando copia de respaldo..."
        cp "$SOLAAR_CONFIG_DIR/rules.yaml" "$SOLAAR_CONFIG_DIR/rules.yaml.bak.$(date +%s)"
    fi
    cp "$SCRIPT_DIR/rules.yaml" "$SOLAAR_CONFIG_DIR/rules.yaml"
    echo "✔ Reglas de automatización copiadas a $SOLAAR_CONFIG_DIR/rules.yaml"
fi

# 4. Configurar inicio automático de Solaar en segundo plano
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat << 'EOF' > "$AUTOSTART_DIR/solaar.desktop"
[Desktop Entry]
Type=Application
Name=Solaar
Comment=Logitech Device Manager
Exec=solaar --window=hide
Icon=solaar
Terminal=false
Categories=Utility;GTK;
StartupNotify=false
EOF
echo "✔ Solaar configurado para iniciar minimizado en el arranque ($AUTOSTART_DIR/solaar.desktop)"

# 5. Configurar atajos de GNOME
echo ""
echo "¿Deseas registrar los atajos de teclado globales en GNOME para los 3 canales?"
echo "  [Super + Alt + 1] -> Canal 1 (Dispositivo 1)"
echo "  [Super + Alt + 2] -> Canal 2 (Dispositivo 2)"
echo "  [Super + Alt + 3] -> Canal 3 (Dispositivo 3)"
read -p "¿Configurar atajos Super+Alt+1/2/3? (S/n): " resp_shortcuts || resp_shortcuts="s"
if [[ ! "$resp_shortcuts" =~ ^[nN]$ ]]; then
    "$SCRIPT_DIR/configure-shortcuts.sh"
fi

echo ""
echo "=========================================================="
echo "🎉 ¡Configuración completada con éxito!"
echo "Revisa el archivo README.md para más detalles sobre cómo"
echo "replicar la configuración en tu segunda laptop."
echo "=========================================================="
