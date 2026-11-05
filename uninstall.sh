#!/usr/bin/env bash
# ==============================================================================
# uninstall.sh - Deshabilitar y Desinstalar LogiPop Sync
# ==============================================================================
# Revierte todas las configuraciones realizadas por setup.sh:
# 1. Elimina los atajos de teclado registrados en GNOME.
# 2. Desactiva el inicio automático de Solaar.
# 3. Elimina las reglas de automatización (~/.config/solaar/rules.yaml).
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "      🧹 Deshabilitando Configuración de LogiPop"
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

# 3. Remover reglas de Solaar
RULES_FILE="$HOME/.config/solaar/rules.yaml"
if [[ -f "$RULES_FILE" ]]; then
    rm -f "$RULES_FILE"
    echo "✔ Archivo de reglas eliminado ($RULES_FILE)."
fi

# 4. Remover acceso directo de LogiPop Emoji Studio
EMOJI_DESKTOP="$HOME/.local/share/applications/logipop-emojis.desktop"
if [[ -f "$EMOJI_DESKTOP" ]]; then
    rm -f "$EMOJI_DESKTOP"
    echo "✔ Acceso directo de emojis eliminado ($EMOJI_DESKTOP)."
fi

echo ""
echo "=========================================================="
echo "✅ ¡Configuración deshabilitada por completo!"
echo "Tus periféricos han vuelto a su comportamiento de fábrica."
echo ""
echo "Nota: Si además deseas desinstalar la aplicación Solaar,"
echo "puedes ejecutar en tu terminal:"
echo "    sudo apt remove --purge solaar"
echo "=========================================================="
