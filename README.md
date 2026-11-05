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
├── emoji-studio/       # 😃 Mini app gráfica GTK3 para Emojis (Exclusivo para Linux)
│   ├── emoji_manager.py
│   ├── send_emoji.py
│   ├── emojis.json
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

Mini aplicación gráfica nativa en **GTK3** para personalizar los 4 botones mecánicos de emojis del lateral derecho del **Logitech POP Keys** y configurar la 5ta tecla (selector general del sistema operativo):

* **4 Teclas Personalizables:** Asigna cualquier emoji con un solo clic desde la paleta por categorías (*Expresiones*, *Gestos*, *Símbolos*, *Trabajo*) o escribe cualquier carácter Unicode.
* **Tecla 5 (Selector Global):** Abre el buscador de emojis nativo del sistema (<kbd>Super</kbd> + <kbd>.</kbd> / <kbd>Ctrl</kbd> + <kbd>.</kbd>).
* **Integración Solaar Automática:** Desvía las teclas y configura las reglas del daemon en segundo plano con solo presionar **"💾 Guardar y Aplicar al Teclado"**.
* **Acceso Directo de Escritorio:** Disponible en el menú de aplicaciones de Ubuntu.

Para más detalles, consulta [**`emoji-studio/README.md`**](emoji-studio/README.md).

---

## 🚀 Instalación Rápida Todo-en-Uno

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

## 🗑️ Desinstalación

Para revertir cualquier configuración o devolver el equipo al estado original:

```bash
./uninstall.sh
```
