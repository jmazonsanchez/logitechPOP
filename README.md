# 🖱️⌨️ LogiPop Suite — Logitech POP Keys & POP Mouse

Solución de software integral, optimización y herramientas de personalización para periféricos **Logitech POP** (teclado `Logi POP Keys` y ratón `Logi POP Mouse`).

> 📖 **¿Buscas el manual técnico detallado?** Consulta el [**Manual de Usuario Completo (MANUAL.md)**](MANUAL.md) con explicaciones a fondo de la arquitectura, protocolo HID++, solvencia de canales y resolución de problemas.

---

## 📂 Organización del Repositorio

El proyecto está organizado en 3 módulos independientes y autodefinidos:

```
LogiPop/
├── linux/              # 🐧 Sincronización Easy-Switch simultánea para Linux (<90ms)
│   ├── switch.py
│   ├── switch-host.sh
│   ├── configure-shortcuts.sh
│   ├── rules.yaml
│   ├── setup.sh
│   ├── uninstall.sh
│   └── README.md
│
├── windows/            # 🪟 Sincronización Easy-Switch simultánea para Windows
│   ├── LogiPop.cs
│   ├── setup.bat
│   ├── uninstall.bat
│   ├── switch.ps1
│   └── README.md
│
├── emoji-studio/       # 😃 Suite gráfica GTK3 para Emojis, Atajos y Dictado por Voz (Linux)
│   ├── emoji_manager.py
│   ├── picker.py
│   ├── dictate.py
│   ├── daemon.py
│   ├── send_emoji.sh
│   ├── send_emoji.py
│   ├── bin/
│   │   ├── setup_whisper.sh
│   │   ├── wl-copy
│   │   └── wl-paste
│   ├── catalog.py
│   ├── theme.py
│   ├── logipop.svg
│   ├── emojis.default.json
│   ├── setup.sh
│   ├── uninstall.sh
│   └── README.md
│
├── setup.sh            # 🚀 Instalador interactivo maestro
├── uninstall.sh        # 🧹 Desinstalador interactivo maestro
├── MANUAL.md           # 📘 Manual técnico y de usuario completo
└── README.md           # 📋 Esta guía principal
```

---

## 🎯 1. Sincronización Easy-Switch Multiplataforma

Permite alternar entre hasta 3 computadoras de forma **simultánea y coordinada** tanto para el teclado como para el ratón con un solo atajo global, eliminando la necesidad de voltear el ratón para cambiar de canal.

| Canal / Host | Asignación | Conexión | Atajo Global |
| :---: | :--- | :--- | :--- |
| **Canal 1** | **Dispositivo 1** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1</kbd> *(Win + Alt + 1)* |
| **Canal 2** | **Dispositivo 2** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> *(Win + Alt + 2)* |
| **Canal 3** | **Dispositivo 3** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>3</kbd> *(Win + Alt + 3)* |

* **En Linux:** Consulta [**`linux/README.md`**](linux/README.md) o ejecuta `./setup.sh` (opción 1 o 3).
* **En Windows:** Consulta [**`windows/README.md`**](windows/README.md) y ejecuta `windows\setup.bat`.

> [!WARNING]
> **Instalación en Todos tus Equipos:** Para conmutar fluidamente en ambas direcciones, instala el proyecto en cada equipo (sea Linux o Windows). La Laptop 1 envía la orden para pasar a la Laptop 2, y la Laptop 2 necesita el script para regresar a la Laptop 1.

---

## 😃 2. LogiPop Emoji Studio (Exclusivo para Linux)

> [!NOTE]
> **¿Por qué es exclusivo para Linux?**
> En Windows y macOS, Logitech ofrece soporte oficial para las teclas de emojis mediante *Logi Options+*. Sin embargo, **en Linux no existe software oficial**, dejando estas teclas completamente inactivas por defecto. **LogiPop Emoji Studio** solventa exclusivamente esta carencia para distribuciones Linux.

Mini aplicación gráfica nativa en **GTK3** para personalizar los 4 botones mecánicos de emojis del lateral derecho del **Logitech POP Keys** y gestionar la 5ta tecla:

* **4 Teclas Personalizables:** Asigna cualquier emoji con un solo clic desde la paleta de 8 categorías completas (+650 emojis Unicode estándar) o escribe cualquier carácter personalizado.
* **Tecla 5 (Mini Selector Flotante):** Despliega una ventana emergente interactiva con biblioteca organizada por categorías, buscador en tiempo real y pegado automático inmediato en tu editor o campo de texto previo.
* **Modo Oscuro / Claro Automático:** Interfaz adaptativa que detecta en tiempo real las preferencias visuales del sistema operativo (GNOME Dark/Light Mode).
* **Latencia Ultrarrápida (<25ms):** Inserción instantánea mediante demonio de teclado virtual persistente (`/dev/uinput`) y socket UNIX local.
* **Integración Solaar Automática:** Desvía las teclas y configura las reglas del daemon en segundo plano con solo presionar **"💾 Guardar y Aplicar al Teclado"**.
* **Acceso Directo e Icono Oficial:** Disponible en el dock y menú de aplicaciones de GNOME con logo oficial vectorizado.

Para más detalles, consulta [**`emoji-studio/README.md`**](emoji-studio/README.md).

---

## 🎙️📸 3. Teclas Especiales de Productividad y Dictado por Voz (Linux)

Además de los emojis y la sincronización entre computadoras, la suite habilita las teclas superiores y de función del POP Keys que normalmente quedan inactivas o desaprovechadas en Linux:

* **Tecla <kbd>F4</kbd> (Captura de Pantalla Completa):** Realiza una captura instantánea de toda la pantalla y la guarda directamente en `~/Imágenes/Capturas de pantalla/` mediante la combinación de sistema <kbd>Shift</kbd> + <kbd>Print</kbd>.
* **Tecla <kbd>F5</kbd> (Seleccionar Recorte de Pantalla):** Abre el selector interactivo de recorte de GNOME (<kbd>Print</kbd>) para capturar un área o ventana específica.
* **Tecla <kbd>F6</kbd> (Silenciar / Reactivar Micrófono):** Envía el evento nativo `KEY_MICMUTE` a PipeWire/ALSA, silenciando o reactivando el micrófono con confirmación visual OSD en pantalla, funcionando en segundo plano sin importar la aplicación enfocada (Zoom, Meet, Teams, Discord).
* **Tecla de Dictado por Voz (entre <kbd>F12</kbd> y <kbd>Supr</kbd>):** Transcripción de voz a texto 100% offline y privada impulsada localmente por **Whisper.cpp**:
  * **1ª pulsación:** Emite un tono auditivo y muestra la notificación *"🎙️ Dictado: Escuchando..."*.
  * **2ª pulsación:** Detiene la grabación, transcribe el audio en tu CPU con el modelo `ggml-tiny.bin` (<1.5s) y pega el texto automáticamente en la aplicación activa.
  * **Watchdog de seguridad:** Se detiene automáticamente a los 35 segundos si olvidas presionar la tecla.

---

## 🚀 4. Instalación Rápida Todo-en-Uno

Desde la raíz del proyecto, ejecuta el asistente interactivo:

```bash
chmod +x setup.sh
./setup.sh
```

El asistente te permitirá elegir:
1. Instalar la sincronización Easy-Switch en Linux.
2. Instalar LogiPop Emoji Studio.
3. Instalar ambos componentes a la vez.

---

## 🔄 5. Actualización en Otros Equipos

Si ya tienes el repositorio clonado e instalado en varios equipos (Laptop 1, Laptop 2, PC, etc.) y deseas aplicar los cambios más recientes:

### 🐧 En Linux (Ubuntu, Debian, Fedora, Arch, etc.):

Abre una terminal en la carpeta del repositorio y ejecuta:

```bash
git pull origin main
./setup.sh --all
```

> [!TIP]
> **¿Qué realiza `./setup.sh --all` al actualizar?**
> * **Reinicia el demonio en segundo plano (`daemon.py`):** Detiene la instancia previa en ejecución e inicia la versión actualizada con las optimizaciones de latencia y el mini selector de emojis (Tecla 5).
> * **Actualiza iconos y accesos directos:** Registra los nuevos logos SVG y PNGs multi-resolución en `~/.local/share/icons/` y actualiza la caché del entorno de escritorio.
> * **Actualiza reglas de Solaar:** Aplica la configuración silenciosa (sin alertas `notify-send` en pantalla) de manera inmediata.

### 🪟 En Windows:

1. Abre **PowerShell** o **Git Bash** en la carpeta del repositorio:
   ```powershell
   git pull origin main
   ```
2. Ejecuta el script de instalación (o haz doble clic sobre él en el explorador de archivos):
   ```cmd
   windows\setup.bat
   ```
> Esto recompilará automáticamente el binario `LogiPop.exe`, actualizará la versión residente en `%APPDATA%\LogiPop\` y reiniciará el servicio en segundo plano.

---

## 🗑️ 6. Desinstalación

Para revertir cualquier configuración o devolver el equipo al estado original:

```bash
./uninstall.sh
```

---

## 🤝 Créditos y Colaboradores

* **Autor y Desarrollo Principal:** [@jmazonsanchez](https://github.com/jmazonsanchez)
* **Pair Programming y Asistencia Técnica:** [Antigravity](https://deepmind.google/) — Advanced Agentic Coding (Google DeepMind)

