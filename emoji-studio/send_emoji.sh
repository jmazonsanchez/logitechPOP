#!/bin/sh
# ==============================================================================
# send_emoji.sh - Disparador ultrarrápido para LogiPop (< 3ms de latencia)
# ==============================================================================

KEY="${1:-1}"
UID_VAL="$(id -u)"
SOCK="${XDG_RUNTIME_DIR:-/run/user/$UID_VAL}/logipop_emoji_${UID_VAL}.sock"

# 1. Envío ultrarrápido vía UNIX socket usando netcat (~3ms)
if command -v nc >/dev/null 2>&1; then
    if printf "%s\n" "$KEY" | nc -U -w 1 "$SOCK" >/dev/null 2>&1; then
        exit 0
    fi
fi

# 2. Si el socket no responde o nc falla, respaldo en Python
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/send_emoji.py" "$KEY"
