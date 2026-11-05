#!/usr/bin/env bash
# ==============================================================================
# configure-shortcuts.sh - Register GNOME Global Shortcuts for LogiPop (3 Channels)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SWITCH_SCRIPT="$SCRIPT_DIR/switch-host.sh"

if [[ ! -x "$SWITCH_SCRIPT" ]]; then
    chmod +x "$SWITCH_SCRIPT"
fi

echo "⌨️ Configurando atajos globales de GNOME para los 3 canales de LogiPop..."

if ! command -v gsettings >/dev/null 2>&1; then
    echo "⚠️ 'gsettings' no encontrado."
    exit 1
fi

MEDIA_SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
CUSTOM_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"

# Configuración por defecto de los 3 canales soportados por el hardware Logitech POP
declare -A SHORTCUTS=(
    ["logipop-c1"]="LogiPop -> Dispositivo 1|$SWITCH_SCRIPT 1 'Dispositivo 1'|<Super><Alt>1"
    ["logipop-c2"]="LogiPop -> Dispositivo 2|$SWITCH_SCRIPT 2 'Dispositivo 2'|<Super><Alt>2"
    ["logipop-c3"]="LogiPop -> Dispositivo 3|$SWITCH_SCRIPT 3 'Dispositivo 3'|<Super><Alt>3"
)

NEW_PATHS=()

for ID in "${!SHORTCUTS[@]}"; do
    IFS="|" read -r NAME CMD BIND <<< "${SHORTCUTS[$ID]}"
    PATH_ENTRY="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/$ID/"
    
    gsettings set "$CUSTOM_SCHEMA:$PATH_ENTRY" name "$NAME"
    gsettings set "$CUSTOM_SCHEMA:$PATH_ENTRY" command "$CMD"
    gsettings set "$CUSTOM_SCHEMA:$PATH_ENTRY" binding "$BIND"
    
    NEW_PATHS+=("'$PATH_ENTRY'")
    echo "  ✔ Registrado: $BIND -> $NAME"
done

# Actualizar lista en gsettings
python3 -c "
import subprocess

media_schema = '$MEDIA_SCHEMA'
required = [
    \"'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c1/'\",
    \"'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c2/'\",
    \"'/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c3/'\"
]

current_raw = subprocess.check_output(['gsettings', 'get', media_schema, 'custom-keybindings']).decode().strip()
items = []
if current_raw.startswith('[') and current_raw.endswith(']'):
    content = current_raw[1:-1].strip()
    if content:
        items = [x.strip() for x in content.split(',') if x.strip()]

for req in required:
    if req not in items:
        items.append(req)

new_val = '[' + ', '.join(items) + ']'
subprocess.check_call(['gsettings', 'set', media_schema, 'custom-keybindings', new_val])
"

echo ""
echo "🎉 ¡Los 3 atajos quedaron configurados exitosamente en GNOME!"
echo "  [Super + Alt + 1] ➔ Conectar teclado y mouse a Dispositivo 1"
echo "  [Super + Alt + 2] ➔ Conectar teclado y mouse a Dispositivo 2"
echo "  [Super + Alt + 3] ➔ Conectar teclado y mouse a Dispositivo 3"
