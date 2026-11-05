#!/usr/bin/env bash
# ==============================================================================
# uninstall.sh - Desinstalador Principal de LogiPop
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "          🧹 Desinstalador de Suite Logitech POP"
echo "=========================================================="
echo ""
echo "Selecciona qué componente deseas desinstalar:"
echo ""
echo "  1) Desinstalar Sincronización Easy-Switch (Linux)"
echo "  2) Desinstalar LogiPop Emoji Studio"
echo "  3) Desinstalar Todo (Revertir al estado de fábrica)"
echo "  4) Salir"
echo ""

read -p "Opción [1-4] (por defecto 3): " opt || opt="3"
opt="${opt:-3}"

case "$opt" in
    1)
        echo ""
        "$SCRIPT_DIR/linux/uninstall.sh"
        ;;
    2)
        echo ""
        "$SCRIPT_DIR/emoji-studio/uninstall.sh"
        ;;
    3)
        echo ""
        "$SCRIPT_DIR/linux/uninstall.sh"
        echo ""
        "$SCRIPT_DIR/emoji-studio/uninstall.sh"
        ;;
    4)
        echo "Operación cancelada."
        exit 0
        ;;
    *)
        echo "Opción no reconocida. Desinstalando todo..."
        "$SCRIPT_DIR/linux/uninstall.sh"
        echo ""
        "$SCRIPT_DIR/emoji-studio/uninstall.sh"
        ;;
esac
