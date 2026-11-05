# 😃 LogiPop Emoji Studio

Aplicación gráfica nativa (GTK3) y motor de inyección de emojis para el teclado mecánico **Logitech POP Keys** en Linux.

---

## 🎨 Visión General

El teclado Logitech POP Keys cuenta con 5 teclas dedicadas en su lateral derecho:
* **4 Teclas Físicas Personalizables** (IDs 260 al 263: *Heart Eyes*, *Crying*, *Smiley*, *Fire/Tears*).
* **1 Tecla de Menú de Emojis** (ID 264: abre el selector completo de emojis de todo el sistema).

```
 ┌───┐ ──> Tecla 1: [ 😍 ] (Personalizable)
 │   │ ──> Tecla 2: [ 😂 ] (Personalizable)
 │   │ ──> Tecla 3: [ 😊 ] (Personalizable)
 │   │ ──> Tecla 4: [ 🔥 ] (Personalizable)
 └───┘ ──> Tecla 5: [ 🌐 ] (Selector Completo de GNOME: Super + .)
```

---

## ✨ Características

1. **Paleta Rápida por Categorías:** Pestañas interactivas con decenas de emojis organizados en *Expresiones*, *Gestos*, *Símbolos* y *Trabajo*.
2. **Entrada Libre de Texto:** Soporta cualquier carácter o símbolo Unicode, banderas y combinaciones.
3. **Prueba en Vivo (`📋 Probar`):** Cada casilla tiene un botón de prueba directa para verificar la inyección inmediata en cualquier aplicación en foco sin tocar el teclado.
4. **Tecla 5 (Selector Global):** Vinculada al atajo de sistema (<kbd>Super</kbd> + <kbd>.</kbd> / <kbd>Ctrl</kbd> + <kbd>.</kbd>).
5. **Integración Transparente con Solaar:** Al presionar **"💾 Guardar y Aplicar al Teclado"**, la aplicación desvía (*divert*) las teclas en el hardware, genera las reglas en `~/.config/solaar/rules.yaml` y recarga Solaar en segundo plano.

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

* [`emoji_manager.py`](emoji_manager.py): Interfaz gráfica GTK3 con paleta de emojis y asistente de integración.
* [`send_emoji.py`](send_emoji.py): Motor backend que escribe al portapapeles (Wayland/X11) y simula pulsaciones mediante `/dev/uinput`.
* [`emojis.json`](emojis.json): Archivo de persistencia JSON de los 4 emojis configurados.
* [`setup.sh`](setup.sh): Instalador del lanzador `.desktop` e integración inicial.
* [`uninstall.sh`](uninstall.sh): Desinstalador limpio.
