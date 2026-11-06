# 😃 LogiPop Emoji Studio (Exclusivo para Linux)

> [!IMPORTANT]
> **Herramienta Exclusiva para Linux:** Esta utilidad está diseñada especialmente para resolver la falta de soporte oficial de Logitech en distribuciones Linux (Ubuntu, Debian, Fedora, Arch, etc.). En Windows y macOS, Logitech ya incluye soporte nativo para los emojis del POP Keys mediante su suite oficial *Logi Options+*.

Aplicación gráfica nativa (GTK3) y motor de inyección de emojis para el teclado mecánico **Logitech POP Keys** en Linux.

---

## 🎨 Visión General

El teclado Logitech POP Keys cuenta con 5 teclas dedicadas en su lateral derecho:
* **4 Teclas Físicas Personalizables** (IDs 260 al 263: *Heart Eyes*, *Crying*, *Smiley*, *Fire/Tears*).
* **1 Tecla de Menú de Emojis** (ID 264: abre el mini selector completo con categorías, buscador y auto-pegado).

```
 ┌───┐ ──> Tecla 1: [ 😍 ] (Personalizable)
 │   │ ──> Tecla 2: [ 😂 ] (Personalizable)
 │   │ ──> Tecla 3: [ 😊 ] (Personalizable)
 │   │ ──> Tecla 4: [ 🔥 ] (Personalizable)
 └───┘ ──> Tecla 5: [ 🎛️ ] (Mini Selector Flotante: Categorías + Búsqueda + Auto-pegado)
```

---

## ✨ Características

1. **Paleta Rápida por 8 Categorías:** Más de 650 emojis estándar organizados en pestañas temáticas (*Caras y Emociones*, *Gestos y Personas*, *Animales y Naturaleza*, *Comida y Bebida*, *Actividades*, *Viajes*, *Objetos*, *Símbolos y Banderas*).
2. **Entrada Libre de Texto:** Soporta cualquier carácter o símbolo Unicode, banderas y combinaciones especiales.
3. **Tecla 5 (Mini Selector Flotante):** Despliega al instante una ventana emergente interactiva con biblioteca categorizada, filtro de búsqueda en tiempo real y auto-pegado inmediato en la aplicación previa. Se puede cerrar en cualquier momento con <kbd>Esc</kbd> o pulsando de nuevo la Tecla 5 (toggle).
4. **Modo Oscuro / Claro Automático:** Detecta en tiempo real la preferencia de tema del sistema (GNOME Dark/Light Mode) y adapta los estilos visuales de la interfaz.
5. **Inyección Ultrarrápida (<25ms):** La pulsación física se transmite mediante un script POSIX (`send_emoji.sh`) a través de un socket UNIX a un demonio persistente (`daemon.py`), el cual simula `Ctrl+V` mediante el teclado virtual del kernel `/dev/uinput` sin demoras perceptibles.
6. **Prueba en Vivo (`📋 Probar`):** Cada casilla tiene un botón de prueba directa para verificar la inyección inmediata en cualquier aplicación en foco sin tocar el teclado.
7. **Integración Transparente con Solaar:** Al presionar **"💾 Guardar y Aplicar al Teclado"**, la aplicación desvía (*divert*) las teclas en el hardware, genera las reglas en `~/.config/solaar/rules.yaml` y notifica al demonio en memoria sin demoras.
8. **Iconos Nativos en el Sistema:** Instala iconos vectoriales SVG y mapas de bits PNG multi-resolución en `~/.local/share/icons/hicolor` para una integración visual limpia en el dock y menú de aplicaciones.
9. **Tecla F4 (Captura de Pantalla Completa):** Realiza una captura instantánea de toda la pantalla y la guarda directamente en tu carpeta de Imágenes (<kbd>Shift</kbd> + <kbd>Print</kbd>).
10. **Tecla F5 (Seleccionar Recorte de Pantalla):** Abre el selector interactivo de GNOME para recortar y capturar un área específica de la pantalla (<kbd>Print</kbd>).
11. **Tecla F6 (Silenciar Micrófono):** Silencia o reactiva el micrófono de todo el sistema operativo (PipeWire) con indicación visual OSD en pantalla, funcionando instantáneamente en Zoom, Google Meet, Teams o Discord sin cambiar de ventana.
12. **Tecla de Dictado / Comando de Voz (entre F12 y Supr):** Dictado de voz a texto 100% privado y offline impulsado por **Whisper.cpp**. Al presionar la tecla, emite un aviso sonoro y visual (*"🎙️ Escuchando..."*); al pulsarla nuevamente (o tras 35s), transcribe el audio en tu CPU local y pega el texto directamente en la aplicación enfocada sin enviar un solo byte a la nube.

---

## 🚀 Instalación y Puesta en Marcha

Para instalar el lanzador en el menú de aplicaciones y configurar las reglas iniciales:

```bash
cd emoji-studio
chmod +x setup.sh
./setup.sh
```

### ¿Cómo abrir la aplicación?
* **Desde el Menú de Aplicaciones:** Busca *"LogiPop Emoji Studio"* o *"Emojis"*.
* **Desde la Terminal:**
  ```bash
  python3 emoji-studio/emoji_manager.py
  ```

---

## 🗑️ Desinstalación

Para eliminar el acceso directo y las reglas de emojis de Solaar:

```bash
cd emoji-studio
./uninstall.sh
```

---

## 📂 Archivos del Módulo

* [`emoji_manager.py`](emoji_manager.py): Aplicación gráfica GTK3 con catálogo de emojis, editor de teclas y asistente de integración.
* [`picker.py`](picker.py): Mini selector flotante emergente con catálogo categorizado, buscador en vivo y auto-pegado.
* [`catalog.py`](catalog.py): Catálogo centralizado con más de 650 emojis organizados por categorías.
* [`theme.py`](theme.py): Gestor de temas claro/oscuro adaptativo para GNOME y Wayland.
* [`daemon.py`](daemon.py): Demonio en segundo plano con teclado virtual persistente (`/dev/uinput`), caché en memoria y socket UNIX.
* [`dictate.py`](dictate.py): Motor de dictado por voz offline con control de estado (toggle), grabación por PipeWire y auto-pegado con Whisper.cpp.
* [`bin/setup_whisper.sh`](bin/setup_whisper.sh): Instalador autónomo y descargador del modelo Whisper.cpp sin requerir permisos de root.
* [`send_emoji.sh`](send_emoji.sh): Disparador POSIX ultrarrápido (<3ms) ejecutado por Solaar para comunicar la pulsación al socket UNIX.
* [`send_emoji.py`](send_emoji.py): Disparador alternativo en Python (respaldo).
* [`logipop.svg`](logipop.svg): Logotipo oficial vectorizado del proyecto.
* [`emojis.default.json`](emojis.default.json): Configuración inicial por defecto (😍 😂 😊 🔥).
* `emojis.json`: Archivo de configuración local generado por la aplicación (ignorado en git).
* [`bin/wl-copy`](bin/): Binario independiente de gestión de portapapeles para entornos Wayland.
* [`setup.sh`](setup.sh): Instalador de iconos, lanzador `.desktop`, servicio de autostart y reglas de Solaar.
* [`uninstall.sh`](uninstall.sh): Desinstalador limpio para revertir todas las configuraciones.
