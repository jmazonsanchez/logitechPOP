# 📘 Manual de Usuario: Sincronización Logitech POP (Keys & Mouse)

> **Guía integral de arquitectura, resolución técnica, configuración, uso, personalización y desinstalación para Linux.**

---

## 📑 Tabla de Contenidos

1. [La Problemática: ¿Por qué ocurre la desincronización?](#1-la-problemática-por-qué-ocurre-la-desincronización)
2. [La Solvencia: ¿Cómo se resuelve técnica y prácticamente?](#2-la-solvencia-cómo-se-resuelve-técnica-y-prácticamente)
3. [Mapeo de Canales del Ecosistema](#3-mapeo-de-canales-del-ecosistema)
4. [Instalación y Activación Paso a Paso](#4-instalación-y-activación-paso-a-paso)
   * [Paso 1: Instalación en Laptop 1 (Principal)](#41-paso-1-instalación-en-laptop-1-principal)
   * [Paso 2: Instalación en Laptop 2 (Segunda Laptop)](#42-paso-2-instalación-en-laptop-2-segunda-laptop)
   * [Paso 3: Vinculación en la Tablet (Android / iPad)](#43-paso-3-vinculación-en-la-tablet-android--ipad)
5. [Modo de Uso Diario](#5-modo-de-uso-diario)
   * [Conmutación Directa con F1, F2 y F3](#51-conmutación-directa-con-f1-f2-y-f3)
   * [Conmutación por Atajo Global (Super + Alt + 1/2)](#52-conmutación-por-atajo-global-super--alt--12)
   * [Dinámica de Entrada y Salida con la Tablet](#53-dinámica-de-entrada-y-salida-con-la-tablet)
6. [Personalización y Modificación de Reglas](#6-personalización-y-modificación-de-reglas)
   * [Estructura del Archivo de Reglas (`rules.yaml`)](#61-estructura-del-archivo-de-reglas-rulesyaml)
   * [Asignar Otras Teclas (ej. Teclas de Emoji)](#62-asignar-otras-teclas-ej-teclas-de-emoji)
   * [Recarga de Reglas sin Reiniciar](#63-recarga-de-reglas-sin-reiniciar)
7. [Diagnóstico y Resolución de Problemas (Troubleshooting)](#7-diagnóstico-y-resolución-de-problemas-troubleshooting)
8. [Desactivación y Retorno al Estado de Fábrica](#8-desactivación-y-retorno-al-estado-de-fábrica)

---

## 1. La Problemática: ¿Por qué ocurre la desincronización?

Los periféricos **Logitech POP Keys** (teclado) y **Logitech POP Mouse** (ratón) cuentan con conectividad multidispositivo (*Easy-Switch*) para alternar entre hasta 3 terminales distintas. Sin embargo, su diseño de fábrica presenta serias limitaciones operativas:

### 1. Ausencia de enlace directo entre periféricos
El ratón y el teclado **no se comunican entre sí**. No cuentan con una red inalámbrica privada (*mesh* o punto a punto) que enlace un dispositivo con el otro. Cada uno es un periférico Bluetooth Low Energy (BLE) o Logi Bolt independiente que solo sabe hablar con la computadora anfitriona (*Host*) a la que está conectado en ese momento.

### 2. Asimetría física y fricción ergonómica
* **En el teclado:** Cambiar de dispositivo es cómodo e inmediato; basta presionar las teclas <kbd>F1</kbd>, <kbd>F2</kbd> o <kbd>F3</kbd> situadas en la fila superior.
* **En el ratón:** El botón de cambio está ubicado en la **base inferior**. Para cambiar de canal, el usuario se ve obligado a suspender su trabajo, levantar el ratón, darle la vuelta, pulsar un botón diminuto y mirar si el LED indicador parpadeó en el canal 1, 2 o 3.

### 3. El error constante de canal cruzado
Dado que ambos periféricos cambian de manera independiente, es muy frecuente que el usuario presione <kbd>F2</kbd> en el teclado creyendo que todo su entorno cambió, pero el ratón sigue anclado al canal 1. El resultado es frustración inmediata: intentar mover el cursor en una pantalla mientras se teclea en otra diferente.

### 4. Falta de soporte oficial de software en Linux
En Windows y macOS, Logitech ofrece la suite *Logi Options+* con su módulo *Flow*, el cual permite coordinar el salto de periféricos al mover el ratón al borde de la pantalla. Sin embargo, **Logitech no proporciona soporte ni aplicación oficial para Linux**, dejando a los usuarios de este sistema sin una solución nativa para sincronizar sus dispositivos.

---

## 2. La Solvencia: ¿Cómo se resuelve técnica y prácticamente?

La solución no requiere abrir el hardware ni reprogramar microcontroladores cerrados. Se resuelve **a nivel de software de sistema y protocolo anfitrión** mediante el estándar abierto **Logitech HID++** y la herramienta de gestión **Solaar**:

```
                       [ Laptop Linux ]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [ Solaar Daemon ]             [ Atajos GNOME ]
               │                             │
    Escucha evento F1/F2/F3          Dispara switch-host.sh
               │                             │
               └──────────────┬──────────────┘
                              │
         Envía orden HID++ paralela (Feature 0x1814)
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [ Logi POP Mouse ]            [ Logi POP Keys ]
       (Salta de canal)              (Salta de canal)
```

### 1. Protocolo Logitech HID++ (`Feature 0x1814 - Change Host`)
Tanto el POP Keys como el POP Mouse implementan el protocolo oficial de comunicación extendida HID++. Dentro de este protocolo existe la característica `0x1814`, que permite a una aplicación anfitriona consultar y ordenar por software el cambio inmediato de canal Bluetooth.

### 2. Automatización reactiva mediante Reglas de Solaar
A través del archivo de reglas `rules.yaml`:
* Cuando el usuario presiona y suelta la tecla <kbd>F1</kbd>, <kbd>F2</kbd> o <kbd>F3</kbd> en el POP Keys, el teclado emite el evento de hardware `Host Switch Channel`.
* El motor de reglas de Solaar intercepta este evento en milisegundos y despacha la orden `Set: change-host` al POP Mouse.
* **Resultado:** Al presionar la tecla del teclado, el ratón salta de forma instantánea al mismo equipo, sin tener que tocarlo.

### 3. Ejecución simultánea y en paralelo
Para evitar que el teclado corte la sesión Bluetooth antes de que el ratón procese el mensaje, el script disparador ejecuta ambas órdenes en hilos paralelos concurrentes (`&`), garantizando que ambos periféricos reciban la orden en el mismo instante.

### 4. Independencia del Hardware y Reversibilidad Total
El método no flashea ni altera memorias no volátiles. Si en algún momento se desea volver al comportamiento de fábrica, basta desinstalar el script y las reglas; los periféricos vuelven a su estado original al 100%.

---

## 3. Mapeo de Canales del Ecosistema

Para operar de forma consistente, se establece la siguiente matriz de canales fijos:

| Canal | Dispositivo Destino | Tipo de Conexión | Rol en el Ecosistema |
| :---: | :--- | :---: | :--- |
| **Canal 1** | **Laptop Linux 1** | Bluetooth BLE | Laptop principal de trabajo |
| **Canal 2** | **Laptop Linux 2** | Bluetooth BLE | Segunda laptop de desarrollo |
| **Canal 3** | **Tablet** | Bluetooth BLE | Dispositivo móvil (Android / iPad) |

---

## 4. Instalación y Activación Paso a Paso

Toda la solución está empaquetada dentro de la carpeta principal del proyecto: `LogiPop`.

> [!IMPORTANT]
> **Compatibilidad de Sistemas: Exclusivo para Linux**
> El script `setup.sh` y las herramientas de este proyecto están diseñados **únicamente para distribuciones Linux** (Ubuntu, Debian y derivados con GNOME).
> * **¿Por qué solo Linux?** Porque utiliza herramientas propias del entorno Linux como `apt`, `solaar`, `gsettings` y archivos `.desktop` de autostart.
> * **¿Qué pasa en Windows?** En **Windows** (y macOS) **no se necesita este script**, ya que Logitech sí ofrece soporte oficial con su propia aplicación nativa: **Logi Options+**. En Windows, dicha app incluye la función **Logitech Flow**, que permite enlazar el teclado al ratón de forma nativa.
> * Este proyecto existe precisamente para dar a los usuarios de Linux una solución potente, ligera y transparente ante la falta de soporte oficial de Logitech en este sistema.

### 4.1. Paso 1: Instalación en Laptop 1 (Principal)

1. **Instalar Solaar y reglas de permisos:**
   ```bash
   sudo apt update && sudo apt install -y solaar
   ```
   *(La instalación añade las reglas `udev` oficiales de Logitech que dan acceso al protocolo HID++ sin requerir permisos de superusuario).*

2. **Ejecutar el configurador:**
   Accede a la carpeta principal `LogiPop` y ejecuta:
   ```bash
   cd LogiPop
   ./setup.sh
   ```
   El instalador realizará:
   * Asignación de permisos de ejecución a los scripts auxiliares.
   * Instalación de `rules.yaml` en la ruta de configuración de Solaar (`~/.config/solaar/rules.yaml`).
   * Configuración de inicio automático en segundo plano para que Solaar arranque minimizado al encender la PC.
   * Registro de los atajos globales en GNOME (<kbd>Super</kbd>+<kbd>Alt</kbd>+<kbd>1/2</kbd>).

---

### 4.2. Paso 2: Instalación en Laptop 2 (Segunda Laptop)

Para que la conmutación sea **bidireccional** (poder ir de Laptop 1 a Laptop 2 y luego regresar de Laptop 2 a Laptop 1):

1. **Emparejar ambos periféricos en el Canal 2 de la Laptop 2:**
   * En el teclado: Mantén presionado <kbd>F2</kbd> durante 3 segundos hasta que el LED parpadee rápidamente, y vincúlalo en los ajustes de Bluetooth de la Laptop 2.
   * En el ratón: Presiona el botón inferior hasta encender el LED 2, mantenlo presionado 3 segundos y vincúlalo en la Laptop 2.
2. **Copiar la carpeta `LogiPop` a la Laptop 2:**
   Copia la carpeta principal `LogiPop` mediante red local, git o unidad USB.
3. **Instalar en la Laptop 2:**
   ```bash
   sudo apt update && sudo apt install -y solaar
   cd LogiPop
   ./setup.sh
   ```

---

### 4.3. Paso 3: Vinculación en la Tablet (Android / iPad)

1. En el teclado, mantén presionado <kbd>F3</kbd> durante 3 segundos hasta que parpadee rápido.
2. En el ratón, sitúate en el LED 3 con el botón inferior y mantén presionado 3 segundos hasta que parpadee rápido.
3. Abre los Ajustes de Bluetooth de tu tablet y vincula ambos dispositivos.
4. *(No se requiere instalar ninguna aplicación en la tablet; funcionará con los controladores nativos de Bluetooth).*

---

## 5. Modo de Uso Diario

### 5.1. Conmutación Directa con <kbd>F1</kbd>, <kbd>F2</kbd> y <kbd>F3</kbd>
Es el método predeterminado y más ágil:
* Presiona **<kbd>F1</kbd>** en el teclado ➔ Teclado y ratón cambian juntos a la **Laptop 1**.
* Presiona **<kbd>F2</kbd>** en el teclado ➔ Teclado y ratón cambian juntos a la **Laptop 2**.
* Presiona **<kbd>F3</kbd>** en el teclado ➔ Teclado y ratón cambian juntos a la **Tablet**.

> [!NOTE]
> La regla está calibrada para activarse al **soltar la tecla** (`released`). Esto evita colisiones entre el envío de la señal del teclado y el apagado del enlace Bluetooth.

---

### 5.2. Conmutación por Atajo Global (<kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1 / 2</kbd>)
El cambio coordinado más rápido y fiable se realiza mediante:
* <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>1</kbd> ➔ Fuerza el cambio sincronizado a **Laptop 1**.
* <kbd>Super</kbd> + <kbd>Alt</kbd> + <kbd>2</kbd> ➔ Fuerza el cambio sincronizado a **Laptop 2**.

Este atajo ejecuta internamente `switch-host.sh` y el conmutador nativo `switch.py` (< 90ms), realizando la conmutación de forma completamente silenciosa, limpia e inmediata.

---

### 5.3. Dinámica de Entrada y Salida con la Tablet

* **Hacia la Tablet (desde Laptop 1 o 2):**
  Presionas <kbd>F3</kbd> en el teclado. Ambos dispositivos saltan a la tablet automáticamente.
* **Regreso desde la Tablet (hacia Laptop 1 o 2):**
  Dado que los sistemas móviles no permiten software de fondo para redirigir el ratón:
  1. En el teclado, presiona **<kbd>F1</kbd>** o **<kbd>F2</kbd>**.
  2. En el ratón, presiona **una sola vez el botón inferior** para pasarlo al canal 1 o 2.
  3. Al llegar a cualquiera de las dos laptops, la sincronización total queda nuevamente habilitada.

---

## 6. Personalización y Modificación de Reglas

### 6.1. Estructura del Archivo de Reglas (`linux/rules.yaml`)
El archivo de reglas se encuentra en la carpeta `linux/rules.yaml`. Su estructura es:

```yaml
%YAML 1.3
---
- Rule:
    - Key: [Host Switch Channel 1, released]
    - Set: ["Logi POP Mouse", change-host, 1]
---
- Rule:
    - Key: [Host Switch Channel 2, released]
    - Set: ["Logi POP Mouse", change-host, 2]
---
- Rule:
    - Key: [Host Switch Channel 3, released]
    - Set: ["Logi POP Mouse", change-host, 3]
```

---

### 6.2. Personalización de Emojis con LogiPop Emoji Studio
El teclado Logitech POP Keys cuenta con 5 teclas dedicadas en el borde lateral derecho:
* **4 teclas mecánicas intercambiables** (por defecto identificadas con caras de emojis).
* **1 tecla inferior** con el icono de menú de emojis para desplegar la biblioteca completa.

El proyecto incluye una aplicación gráfica nativa llamada **LogiPop Emoji Studio** (`emoji_manager.py`) diseñada para gestionar estas teclas de manera visual:

#### Funcionalidades de la aplicación:
1. **Asignación rápida de emojis:** Cuenta con 4 pestañas de selección rápida (*Expresiones*, *Gestos*, *Símbolos*, *Trabajo*). Haz clic en cualquier tecla de la ventana y luego en el emoji deseado de la paleta.
2. **Compatibilidad Unicode total:** Puedes escribir directamente cualquier emoji compuesto, bandera o símbolo especial en las casillas.
3. **Botón de prueba integrado (`📋 Probar`):** Permite verificar la inyección del emoji en tiempo real sin requerir pulsar físicamente la tecla del teclado.
4. **Soporte para el Selector General de Emojis:** La 5ta tecla está vinculada al selector del sistema operativo mediante el atajo nativo (<kbd>Super</kbd> + <kbd>.</kbd> / <kbd>Ctrl</kbd> + <kbd>.</kbd>).
5. **Aplicación automática a Solaar:** Al presionar **"💾 Guardar y Aplicar al Teclado"**, la aplicación:
   * Guarda los emojis en `emojis.json`.
   * Actualiza el parámetro `divert-keys` en `~/.config/solaar/config.yaml` asignando el valor `1` (Diverted) a las teclas 260, 261, 262, 263 y 264.
   * Genera las reglas en `~/.config/solaar/rules.yaml` vinculando cada pulsación con `send_emoji.py`.
   * Reinicia el demonio Solaar en segundo plano para que los cambios surtan efecto de inmediato.

#### Cómo abrir la aplicación:
* Desde el menú de aplicaciones de tu escritorio GNOME buscando **"LogiPop Emoji Studio"**.
* O directamente desde la terminal con:
  ```bash
  python3 emoji-studio/emoji_manager.py
  ```

---

### 6.3. Recarga de Reglas sin Reiniciar
Cada vez que realices cambios en `rules.yaml`, copia el archivo y recarga el servicio sin reiniciar la sesión:

```bash
cp linux/rules.yaml ~/.config/solaar/rules.yaml
pkill solaar && solaar --window=hide &
```

---

## 7. Diagnóstico y Resolución de Problemas (Troubleshooting)

### 1. El ratón no sigue al teclado
* **Comprueba si Solaar está activo en segundo plano:**
  ```bash
  pgrep -a solaar
  ```
  Si no devuelve ningún proceso, inícialo con: `solaar --window=hide &`.
* **Prueba el cambio por línea de comandos directamente:**
  Desde la carpeta del proyecto, ejecuta:
  ```bash
  ./linux/switch-host.sh 2
  ```
  Si el script cambia ambos dispositivos pero la tecla física F2 no lo hace, revisa que el archivo `~/.config/solaar/rules.yaml` exista y coincida con el provisto en el proyecto.

### 2. Permisos del protocolo HID++ (`/dev/hidraw*`)
Si Solaar no detecta los nombres de los dispositivos, asegúrate de que tu usuario forme parte del grupo `plugdev`:
```bash
groups | grep plugdev
```
Si no aparece, agrégalo y reinicia tu sesión:
```bash
sudo usermod -aG plugdev $USER
```

---

## 8. Desactivación y Retorno al Estado de Fábrica

Si por cualquier razón deseas dejar de utilizar esta solución, la reversión es total, inmediata y limpia:

```bash
cd LogiPop
./uninstall.sh
```

### Acciones ejecutadas por el desinstalador:
1. Elimina los atajos registrados en GNOME (`<Super><Alt>1/2`).
2. Elimina el archivo de inicio automático (`~/.config/autostart/solaar.desktop`).
3. Elimina las reglas de seguimiento (`~/.config/solaar/rules.yaml`).

### (Opcional) Eliminar el software gestor:
```bash
sudo apt remove --purge solaar
```

> [!IMPORTANT]
> **Garantía de Integridad:** Ni los dispositivos ni el sistema operativo retienen modificaciones ocultas. El ratón y el teclado volverán al 100% a su comportamiento estándar de fábrica.
