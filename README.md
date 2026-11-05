# 🖱️⌨️ LogiPop Sync — Sincronización para Logitech POP Keys & POP Mouse

Solución de software y automatización para periféricos **Logitech POP** en Linux, permitiendo cambiar de equipo (*Easy-Switch*) de forma **simultánea y coordinada** tanto para el teclado (`Logi POP Keys`) como para el ratón (`Logi POP Mouse`), evitando tener que voltear el ratón para cambiar de canal.

> 📖 **¿Buscas el manual técnico detallado?** Consulta el [**Manual de Usuario Completo (MANUAL.md)**](MANUAL.md) con explicaciones a fondo de la problemática, la solvencia técnica, arquitectura de eventos y desinstalación.

> [!IMPORTANT]
> **Soporte Exclusivo para Linux:** Este proyecto y el script `setup.sh` están diseñados específicamente para distribuciones **Linux** (Ubuntu, Debian y derivados con GNOME). Si utilizas **Windows**, no necesitas este script ni Solaar, ya que Logitech ofrece soporte oficial nativo mediante su propia aplicación **Logi Options+** (que incluye la función *Logitech Flow* para enlazar teclado y ratón).

> [!WARNING]
> **Instalación Obligatoria en Todos los Equipos Linux:** Para que la conmutación funcione de manera fluida y bidireccional, **debes instalar y ejecutar este proyecto en cada uno de tus dispositivos Linux**. Al estar en la Laptop 1, esta es la que envía la orden para saltar a la Laptop 2; y cuando estés trabajando en la Laptop 2, necesitarás tener instalado el proyecto allí para que pueda enviar la orden de regreso hacia la Laptop 1.

---

## 🎯 Arquitectura de Canales (Hasta 3 Dispositivos)

Por diseño de hardware, los periféricos Logitech POP admiten hasta **3 canales independientes**:

| Canal / Host | Asignación | Conexión | Atajo Global |
| :---: | :--- | :--- | :--- |
| **Canal 1** | **Dispositivo 1** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1</kbd> |
| **Canal 2** | **Dispositivo 2** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> |
| **Canal 3** | **Dispositivo 3** | Bluetooth BLE | <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>3</kbd> |

---

## 🚀 ¿Cómo funciona?

1. **Protocolo Logitech HID++ (`change-host`):**
   A través del script ultrarrápido [`switch.py`](switch.py), se envía la instrucción directa de hardware HID++ `0x1814` a `/dev/hidraw0` y `/dev/hidraw1` de forma concurrente, logrando un tiempo de respuesta inferior a **90 milisegundos**.
2. **Atajos Globales Unificados (<kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>Num</kbd>):**
   Para evitar cualquier conflicto con las aplicaciones ancladas en la barra lateral de Ubuntu (Dock), el cambio coordinado viene preconfigurado para los 3 canales:
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1</kbd> ➔ Conectar ambos periféricos al **Dispositivo 1**
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> ➔ Conectar ambos periféricos al **Dispositivo 2**
   * <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>3</kbd> ➔ Conectar ambos periféricos al **Dispositivo 3**

---

## 📋 Requisitos Previos

En cualquier laptop Linux donde vayas a usar la sincronización, necesitas tener instalado **Solaar**:

```bash
sudo apt update
sudo apt install -y solaar
```

*(Al instalar Solaar, Ubuntu añade automáticamente las reglas udev para permitir comunicación directa con el protocolo HID++).*

---

## ⚙️ Instalación y Puesta en Marcha

### 1. En la Primera Laptop:
Ejecuta el script maestro dentro de la carpeta del proyecto:

```bash
cd logitechPOP
./setup.sh
```

El script se encargará de:
1. Dar permisos de ejecución a las utilidades.
2. Instalar el archivo `rules.yaml` en `~/.config/solaar/rules.yaml`.
3. Configurar el inicio de Solaar en segundo plano al iniciar sesión.
4. Registrar los atajos de teclado en GNOME (<kbd>Super</kbd>+<kbd>Alt</kbd>+<kbd>1/2/3</kbd>).

---

### 2. En la Segunda Laptop (y demás equipos Linux):
Clona este repositorio en tu otro equipo y ejecuta el mismo instalador:

```bash
git clone git@github.com:jmazonsanchez/logitechPOP.git
cd logitechPOP
./setup.sh
```

De esta forma, cuando estés trabajando en el otro equipo, podrás presionar <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> para regresar instantáneamente a la laptop principal.

---

## 🗑️ ¿Cómo deshabilitar o desinstalar esta solución?

Si en cualquier momento decides que ya no quieres usar este método, puedes volver al estado de fábrica al 100% de forma limpia y en un solo segundo:

```bash
cd logitechPOP
./uninstall.sh
```

El script se encargará de:
1. Eliminar los atajos globales de GNOME.
2. Quitar Solaar del inicio automático.
3. Eliminar las reglas de automatización de `~/.config/solaar/rules.yaml`.

Tus periféricos volverán inmediatamente a funcionar exactamente como venían de fábrica.
Si además deseas desinstalar el paquete Solaar del sistema:
```bash
sudo apt remove --purge solaar
```

---

## 🛠️ Estructura del Proyecto

* [`switch.py`](switch.py): Conmutador nativo en Python ultrarrápido (<90ms) que escribe directamente a `/dev/hidraw`.
* [`switch-host.sh`](switch-host.sh): Script wrapper con notificaciones visuales en pantalla (OSD).
* [`configure-shortcuts.sh`](configure-shortcuts.sh): Registrador de atajos de teclado nativos para GNOME (<kbd>Super</kbd>+<kbd>Alt</kbd>+<kbd>Num</kbd>).
* [`setup.sh`](setup.sh): Instalador desatendido / interactivo todo-en-uno.
* [`uninstall.sh`](uninstall.sh): Desinstalador limpio para revertir todo al estado original.
