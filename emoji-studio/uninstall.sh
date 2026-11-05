#!/usr/bin/env bash
# ==============================================================================
# uninstall.sh - Desinstalador de LogiPop Emoji Studio
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo "      🧹 Desinstalando LogiPop Emoji Studio"
echo "=========================================================="
echo ""

# 1. Remover lanzador de aplicaciones y demonio autostart
EMOJI_DESKTOP="$HOME/.local/share/applications/logipop-emojis.desktop"
if [[ -f "$EMOJI_DESKTOP" ]]; then
    rm -f "$EMOJI_DESKTOP"
    echo "✔ Acceso directo eliminado ($EMOJI_DESKTOP)."
fi

DAEMON_AUTOSTART="$HOME/.config/autostart/logipop-daemon.desktop"
if [[ -f "$DAEMON_AUTOSTART" ]]; then
    rm -f "$DAEMON_AUTOSTART"
    echo "✔ Inicio automático del demonio eliminado ($DAEMON_AUTOSTART)."
fi

# 2. Remover iconos del tema del sistema
ICON_THEME_DIR="$HOME/.local/share/icons/hicolor"
rm -f "$ICON_THEME_DIR/scalable/apps/logipop.svg"
for sz in 256 128 64 48; do
    rm -f "$ICON_THEME_DIR/${sz}x${sz}/apps/logipop.png"
done
gtk-update-icon-cache -f -t "$ICON_THEME_DIR" >/dev/null 2>&1 || true
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "✔ Iconos de 'logipop' removidos del tema del sistema."

# 3. Detener proceso demonio
pkill -f "emoji-studio/daemon.py" || true
rm -f /run/user/*/logipop_emoji_*.sock /tmp/logipop_emoji_*.sock 2>/dev/null || true
echo "✔ Demonio detenido."

# 3. Limpiar reglas de emojis en Solaar
SOLAAR_RULES_FILE="$HOME/.config/solaar/rules.yaml"
if [[ -f "$SOLAAR_RULES_FILE" ]]; then
    python3 -c "
import yaml, os
path = os.path.expanduser('~/.config/solaar/rules.yaml')
emoji_key_names = {
    'Emoji Smiley Heart Eyes',
    'Emoji Crying Face',
    'Emoji Smiley',
    'Emoji Smilie With Tears',
    'Emoji'
}

def is_emoji_rule(doc):
    if not isinstance(doc, list): return False
    for comp in doc:
        if isinstance(comp, dict):
            if 'Rule' in comp:
                return is_emoji_rule(comp['Rule'])
            if 'Key' in comp:
                k = comp['Key']
                if isinstance(k, list) and len(k) > 0 and k[0] in emoji_key_names:
                    return True
    return False

if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))
    kept = [d for d in docs if d and not is_emoji_rule(d)]
    with open(path, 'w', encoding='utf-8') as f:
        if kept:
            f.write('%YAML 1.3\n')
            yaml.dump_all(kept, f, explicit_start=True, default_flow_style=False, sort_keys=False)
        else:
            f.write('')
" || true
    echo "✔ Reglas de emojis removidas de Solaar."
fi

# 3. Recargar Solaar si está en ejecución
killall -q solaar || true
nohup solaar --window=hide </dev/null &>/dev/null & || true

echo ""
echo "=========================================================="
echo "✅ ¡LogiPop Emoji Studio desinstalado con éxito!"
echo "=========================================================="
