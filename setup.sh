#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Instalador Principal de LogiPop
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "          🎛️ Suite de Herramientas Logitech POP"
echo "=========================================================="
echo ""
echo "Selecciona qué componente deseas instalar/configurar:"
echo ""
echo "  1) Sincronización Easy-Switch para Linux (Super+Alt+1/2/3)"
echo "  2) LogiPop Emoji Studio (Configurador gráfico de Emojis)"
echo "  3) Instalar Todo (Sincronización + Emoji Studio)"
echo "  4) Salir"
echo ""

read -p "Opción [1-4] (por defecto 3): " opt || opt="3"
opt="${opt:-3}"

case "$opt" in
    1)
        echo ""
        "$SCRIPT_DIR/linux/setup.sh"
        ;;
    2)
        echo ""
        "$SCRIPT_DIR/emoji-studio/setup.sh"
        ;;
    3)
        echo ""
        "$SCRIPT_DIR/linux/setup.sh"
        echo ""
        "$SCRIPT_DIR/emoji-studio/setup.sh"
        ;;
    4)
        echo "Operación cancelada."
        exit 0
        ;;
    *)
        echo "Opción no reconocida. Ejecutando instalación completa..."
        "$SCRIPT_DIR/linux/setup.sh"
        echo ""
        "$SCRIPT_DIR/emoji-studio/setup.sh"
        ;;
esac
