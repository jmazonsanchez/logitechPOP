#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Instalador de LogiPop Emoji Studio
# ==============================================================================

set -euo pipefail

# Verificación de plataforma
if [[ "${OSTYPE:-}" != "linux"* ]]; then
    echo "❌ Error: LogiPop Emoji Studio está diseñado exclusivamente para entornos Linux."
    echo "En Windows, los emojis se configuran a través del software oficial de Logitech (Logi Options+)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      😃 Instalación de LogiPop Emoji Studio"
echo "=========================================================="
echo ""

# 1. Permisos de ejecución
chmod +x "$SCRIPT_DIR/emoji_manager.py" "$SCRIPT_DIR/send_emoji.py" "$SCRIPT_DIR/send_emoji.sh" "$SCRIPT_DIR/daemon.py" "$SCRIPT_DIR/picker.py" "$SCRIPT_DIR/dictate.py" "$SCRIPT_DIR/bin/setup_whisper.sh" "$SCRIPT_DIR/bin/wl-copy" "$SCRIPT_DIR/bin/wl-paste"
echo "✔ Permisos asignados a los scripts y binarios de Emoji Studio."

# 1a. Configurar motor local Whisper.cpp para dictado por voz offline
"$SCRIPT_DIR/bin/setup_whisper.sh" || true

# 1b. Restablecer los emojis por defecto (emojis.json es configuración local, no versionada)
if [[ -f "$SCRIPT_DIR/emojis.json" ]] && ! cmp -s "$SCRIPT_DIR/emojis.default.json" "$SCRIPT_DIR/emojis.json"; then
    EMOJIS_BACKUP="$SCRIPT_DIR/emojis.json.bak.$(date +%s)"
    cp -f "$SCRIPT_DIR/emojis.json" "$EMOJIS_BACKUP"
    echo "ℹ Tu configuración anterior de emojis se respaldó en: $EMOJIS_BACKUP"
fi
cp -f "$SCRIPT_DIR/emojis.default.json" "$SCRIPT_DIR/emojis.json"
echo "✔ Emojis por defecto aplicados (Tecla 1: 😍  2: 😂  3: 😊  4: 🔥)."

# 2. Instalar iconos en el tema del sistema (XDG Icon Theme) para menú, dock y ventana
ICON_THEME_DIR="$HOME/.local/share/icons/hicolor"
mkdir -p "$ICON_THEME_DIR/scalable/apps"
mkdir -p "$ICON_THEME_DIR/256x256/apps"
mkdir -p "$ICON_THEME_DIR/128x128/apps"
mkdir -p "$ICON_THEME_DIR/64x64/apps"
mkdir -p "$ICON_THEME_DIR/48x48/apps"

cp -f "$SCRIPT_DIR/logipop.svg" "$ICON_THEME_DIR/scalable/apps/logipop.svg"

python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

svg_path = '$SCRIPT_DIR/logipop.svg'
icon_base = '$ICON_THEME_DIR'
try:
    pb = GdkPixbuf.Pixbuf.new_from_file(svg_path)
    for sz in [256, 128, 64, 48]:
        scaled = pb.scale_simple(sz, sz, GdkPixbuf.InterpType.BILINEAR)
        scaled.savev(f'{icon_base}/{sz}x{sz}/apps/logipop.png', 'png', [], [])
except Exception:
    pass
"
gtk-update-icon-cache -f -t "$ICON_THEME_DIR" >/dev/null 2>&1 || true
echo "✔ Iconos oficiales 'logipop' instalados en el tema del sistema (SVG + PNG multi-resolución)."

# 3. Instalar lanzador de escritorio .desktop
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat << EOF > "$APP_DIR/logipop-emojis.desktop"
[Desktop Entry]
Type=Application
Name=LogiPop Emoji Studio
GenericName=Configurador de Emojis
Comment=Personalizador de teclas de emojis para Logitech POP Keys
Exec=python3 $SCRIPT_DIR/emoji_manager.py
Icon=logipop
Terminal=false
Categories=Utility;Settings;GTK;
StartupNotify=true
StartupWMClass=logipop-emojis
EOF
chmod +x "$APP_DIR/logipop-emojis.desktop"
update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
echo "✔ Acceso directo 'LogiPop Emoji Studio' instalado en el menú de aplicaciones y dock."

# 4. Configurar inicio automático del demonio en segundo plano
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat << EOF > "$AUTOSTART_DIR/logipop-daemon.desktop"
[Desktop Entry]
Type=Application
Name=LogiPop Emoji Daemon
Comment=Demonio de inyección ultrarrápida de emojis para Logitech POP Keys
Exec=python3 $SCRIPT_DIR/daemon.py
Terminal=false
Categories=Utility;
StartupNotify=false
EOF
echo "✔ Demonio de teclado virtual configurado para inicio automático en el arranque."

# 5. Verificar acceso de escritura a /dev/uinput (teclado virtual del demonio)
# La regla udev de Solaar (60-solaar.rules) otorga el permiso vía 'uaccess', pero solo
# se aplica al arrancar el sistema: si Solaar se instaló después del último arranque,
# /dev/uinput sigue siendo exclusivo de root y los emojis no se insertan.
UINPUT_OK=1
if [[ ! -w /dev/uinput ]]; then
    UINPUT_OK=0
    echo ""
    echo "⚠️  Tu usuario no tiene permiso de escritura sobre /dev/uinput."
    echo "    Sin este permiso el demonio no puede insertar los emojis."

    if grep -qs 'KERNEL=="uinput"' /usr/lib/udev/rules.d/*solaar*.rules /etc/udev/rules.d/*solaar*.rules; then
        echo "    La regla udev de Solaar está instalada pero aún no se ha aplicado"
        echo "    (normalmente porque Solaar se instaló después del último arranque)."

        if [[ -t 0 ]]; then
            read -p "    ¿Aplicarla ahora con sudo? [S/n]: " apply_udev || apply_udev="n"
            if [[ ! "${apply_udev:-S}" =~ ^[nN] ]]; then
                sudo udevadm trigger --action=change --sysname-match=uinput || true
                sudo udevadm settle || true
                if [[ -w /dev/uinput ]]; then
                    UINPUT_OK=1
                    echo "✔ Permiso sobre /dev/uinput aplicado."
                fi
            fi
        fi

        if [[ "$UINPUT_OK" -eq 0 ]]; then
            echo "    Solución: reinicia el equipo, o ejecuta:"
            echo "      sudo udevadm trigger --action=change --sysname-match=uinput"
            echo "    y luego vuelve a correr este instalador."
        fi
    else
        echo "    No se encontró la regla udev de Solaar para uinput."
        echo "    Instala Solaar desde el repositorio de tu distribución (sudo apt install solaar)"
        echo "    y reinicia el equipo antes de volver a correr este instalador."
    fi
    echo ""
fi

# 6. Iniciar o reiniciar el demonio en segundo plano
pkill -f "$SCRIPT_DIR/daemon.py" 2>/dev/null || true
sleep 0.3
# Socket del demonio (misma ruta que daemon.py). Se elimina el sobrante de una instancia
# anterior terminada con SIGTERM para no confundirlo con el de la nueva.
DAEMON_SOCK="${XDG_RUNTIME_DIR:-/tmp}/logipop_emoji_$(id -u).sock"
rm -f "$DAEMON_SOCK"
if [[ "$UINPUT_OK" -eq 1 ]]; then
    nohup python3 "$SCRIPT_DIR/daemon.py" </dev/null &>/dev/null &
    DAEMON_PID=$!

    # Registrar el teclado virtual en uinput toma ~2 s: esperar el socket mientras
    # el proceso siga vivo (si falla, termina antes y se corta la espera), máximo 8 s.
    for _ in $(seq 1 40); do
        [[ -S "$DAEMON_SOCK" ]] && break
        kill -0 "$DAEMON_PID" 2>/dev/null || break
        sleep 0.2
    done
    if [[ -S "$DAEMON_SOCK" ]] && kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo "✔ Demonio de inyección activo en segundo plano."
    else
        UINPUT_OK=0
        echo "⚠️  El demonio no pudo iniciarse. Ejecútalo a mano para ver el error:"
        echo "      python3 $SCRIPT_DIR/daemon.py"
    fi
else
    echo "⏭ Demonio no iniciado: falta el permiso sobre /dev/uinput (arrancará solo tras reiniciar)."
fi

# 7. Aplicar configuración inicial y reglas en Solaar
echo "⚙️ Configurando reglas de teclado en Solaar..."
python3 "$SCRIPT_DIR/emoji_manager.py" --apply || true

echo ""
echo "=========================================================="
if [[ "$UINPUT_OK" -eq 1 ]]; then
    echo "🎉 ¡LogiPop Emoji Studio instalado con éxito!"
else
    echo "⚠️  LogiPop Emoji Studio instalado, pero las teclas de emojis"
    echo "    no funcionarán hasta resolver el permiso de /dev/uinput (ver arriba)."
fi
echo "Puedes abrir la aplicación desde el menú de aplicaciones"
echo "o ejecutando: python3 $SCRIPT_DIR/emoji_manager.py"
echo "=========================================================="
