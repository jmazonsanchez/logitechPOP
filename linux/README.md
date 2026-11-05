# 🐧 LogiPop Sync para Linux

Módulo de sincronización simultánea e instantánea (<90ms) para teclado **Logitech POP Keys** y ratón **Logitech POP Mouse** en Linux (Ubuntu, Debian, Fedora, Arch, etc.).

---

## ⚡ ¿Cómo funciona?

1. **Inyección directa HID++ (`switch.py`):**
   Escribe directamente el paquete raw de 20 bytes del protocolo Logitech HID++ (`Feature 0x1814 - CHANGE_HOST`) en los descriptores `/dev/hidraw*` de ambos periféricos en paralelo. El cambio ocurre en menos de **90 milisegundos**.
2. **Atajos Globales de GNOME (`configure-shortcuts.sh`):**
   Configura atajos nativos en GNOME que no colisionan con el dock de aplicaciones:
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1</kbd> ➔ Canal 1 (Dispositivo 1)
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> ➔ Canal 2 (Dispositivo 2)
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>3</kbd> ➔ Canal 3 (Dispositivo 3)
3. **Conmutación Silenciosa e Inmediata:**
   Cambio de periféricos en segundo plano de manera limpia, sin retrasos ni notificaciones intrusivas en pantalla.

---

## 🚀 Instalación Rápida

Ejecuta el script instalador:

```bash
cd linux
chmod +x setup.sh
./setup.sh
```

El script verificará las dependencias (Solaar para reglas udev), registrará los atajos globales y configurará el inicio automático en segundo plano.

---

## 🗑️ Desinstalación

Para revertir los atajos y el inicio automático:

```bash
cd linux
./uninstall.sh
```

---

## 📂 Archivos del Módulo

* [`switch.py`](switch.py): Script en Python que interactúa directamente con `/dev/hidraw` enviando el paquete HID++.
* [`switch-host.sh`](switch-host.sh): Envoltorio bash que ejecuta `switch.py` de forma limpia y silenciosa.
* [`configure-shortcuts.sh`](configure-shortcuts.sh): Registra o actualiza los 3 atajos globales en `gsettings`.
* [`rules.yaml`](rules.yaml): Reglas de automatización para Solaar.
* [`setup.sh`](setup.sh): Instalador desatendido / interactivo.
* [`uninstall.sh`](uninstall.sh): Desinstalador limpio.
