#!/usr/bin/env bash
# ==============================================================================
# switch-host.sh - LogiPop Simultaneous Easy-Switch Trigger
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_HOST="${1:-}"
LABEL="${2:-}"

if [[ -z "$TARGET_HOST" || ! "$TARGET_HOST" =~ ^[1-3]$ ]]; then
    echo "❌ Error: Debe especificar el número de canal válido (1, 2 o 3)."
    echo "Uso: $0 <1|2|3> [nombre_opcional]"
    exit 1
fi

MSG="Cambiando teclado y mouse al Canal $TARGET_HOST"
if [[ -n "$LABEL" ]]; then
    MSG="$MSG ($LABEL)"
fi

# Notificación visual en pantalla
if command -v notify-send >/dev/null 2>&1; then
    notify-send -i input-keyboard -t 2000 "LogiPop Sync" "$MSG..." || true
fi

echo "🔄 $MSG..."

# Ejecutar el conmutador directo Python (evita bugs de Solaar CLI / D-Bus en Python 3.14)
python3 "$SCRIPT_DIR/switch.py" "$TARGET_HOST"
