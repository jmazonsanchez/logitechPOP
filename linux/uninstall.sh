#!/usr/bin/env bash
# ==============================================================================
# uninstall.sh - Deshabilitar y Desinstalar Sincronización en Linux
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "      🧹 Deshabilitando Sincronización en Linux"
echo "=========================================================="
echo ""

# 1. Eliminar atajos de GNOME
if command -v gsettings >/dev/null 2>&1; then
    MEDIA_SCHEMA="org.gnome.settings-daemon.plugins.media-keys"
    CUSTOM_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"

    echo "⌨️ Removiendo atajos personalizados de GNOME..."

    python3 -c "
import subprocess

media_schema = '$MEDIA_SCHEMA'
custom_schema = '$CUSTOM_SCHEMA'
to_remove = [
    '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c1/',
    '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c2/',
    '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/logipop-c3/'
]

# Leer lista actual
current_raw = subprocess.check_output(['gsettings', 'get', media_schema, 'custom-keybindings']).decode().strip()
items = []
if current_raw.startswith('[') and current_raw.endswith(']'):
    content = current_raw[1:-1].strip()
    if content:
        items = [x.strip() for x in content.split(',') if x.strip()]

# Filtrar
cleaned_items = [item for item in items if not any(rem in item for rem in to_remove)]

# Actualizar lista en gsettings
new_val = '[' + ', '.join(cleaned_items) + ']'
subprocess.check_call(['gsettings', 'set', media_schema, 'custom-keybindings', new_val])

# Resetear las claves individuales
for path in to_remove:
    try:
        subprocess.call(['gsettings', 'reset-recursively', f'{custom_schema}:{path}'])
    except Exception:
        pass
"
    echo "✔ Atajos eliminados de GNOME."
fi

# 2. Eliminar inicio automático de Solaar
AUTOSTART_FILE="$HOME/.config/autostart/solaar.desktop"
if [[ -f "$AUTOSTART_FILE" ]]; then
    rm -f "$AUTOSTART_FILE"
    echo "✔ Inicio automático eliminado ($AUTOSTART_FILE)."
fi

# 3. Remover únicamente reglas de sincronización en Solaar (conservando emojis si existen)
RULES_FILE="$HOME/.config/solaar/rules.yaml"
if [[ -f "$RULES_FILE" ]]; then
    python3 -c "
import yaml, os
path = os.path.expanduser('~/.config/solaar/rules.yaml')
switch_key_names = {
    'Host Switch Channel 1',
    'Host Switch Channel 2',
    'Host Switch Channel 3'
}

def is_switch_rule(doc):
    if not isinstance(doc, list): return False
    for comp in doc:
        if isinstance(comp, dict):
            if 'Rule' in comp:
                return is_switch_rule(comp['Rule'])
            if 'Key' in comp:
                k = comp['Key']
                if isinstance(k, list) and len(k) > 0 and k[0] in switch_key_names:
                    return True
    return False

if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))
    kept = [d for d in docs if d and not is_switch_rule(d)]
    with open(path, 'w', encoding='utf-8') as f:
        if kept:
            f.write('%YAML 1.3\n')
            yaml.dump_all(kept, f, explicit_start=True, default_flow_style=False, sort_keys=False)
        else:
            f.write('')
" || true
    echo "✔ Reglas de sincronización removidas de Solaar."
fi

echo ""
echo "=========================================================="
echo "✅ ¡Sincronización deshabilitada en Linux!"
echo "=========================================================="
