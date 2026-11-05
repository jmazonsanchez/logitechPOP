#!/usr/bin/env bash
# ==============================================================================
# uninstall.sh - Desinstalador Interactivo de la Suite LogiPop
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "          🧹 Desinstalador de Suite Logitech POP"
echo "=========================================================="
echo ""

# Soporte para argumentos de línea de comandos
opt="${1:-}"

if [[ -z "$opt" ]]; then
    echo "¿Qué componente deseas desinstalar?"
    echo ""
    echo "  1) Solo Sincronización Easy-Switch (Linux)"
    echo "     ↳ Desactiva los atajos GNOME (Super+Alt+1/2/3) y reglas de cambio."
    echo "     ↳ Mantiene 'LogiPop Emoji Studio' activo e intacto."
    echo ""
    echo "  2) Solo LogiPop Emoji Studio"
    echo "     ↳ Remueve el acceso directo del menú y las reglas de emojis."
    echo "     ↳ Mantiene la sincronización Easy-Switch activa e intacta."
    echo ""
    echo "  3) Desinstalar Todo por Completo"
    echo "     ↳ Elimina atajos, accesos directos y devuelve todo a estado de fábrica."
    echo ""
    echo "  4) Cancelar y Salir"
    echo ""

    read -p "Elige una opción [1-4] (por defecto 3): " input_opt || input_opt="3"
    opt="${input_opt:-3}"
fi

case "$opt" in
    1|--sync)
        echo "⏳ Desinstalando solo la sincronización Easy-Switch..."
        echo ""
        "$SCRIPT_DIR/linux/uninstall.sh"
        ;;
    2|--emojis|--emoji-studio)
        echo "⏳ Desinstalando solo LogiPop Emoji Studio..."
        echo ""
        "$SCRIPT_DIR/emoji-studio/uninstall.sh"
        ;;
    3|--all)
        echo "⏳ Desinstalando todos los componentes de LogiPop..."
        echo ""
        "$SCRIPT_DIR/linux/uninstall.sh"
        echo ""
        "$SCRIPT_DIR/emoji-studio/uninstall.sh"
        ;;
    4|--cancel)
        echo "Operación cancelada. No se ha modificado nada."
        exit 0
        ;;
    *)
        echo "Opción no reconocida ('$opt'). Operación cancelada."
        exit 1
        ;;
esac
