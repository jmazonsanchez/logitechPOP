#!/usr/bin/env python3
"""
switch.py - Conmutador Ultrarrápido de Canal Logitech HID++
Ejecución directa sobre /dev/hidraw sin esperas ni dependencias pesadas (latencia < 5ms).
"""

import sys
import os
import glob

def fast_switch(target_host_index: int) -> bool:
    """
    target_host_index: 0 (Canal 1), 1 (Canal 2), 2 (Canal 3)
    """
    devices_switched = 0

    # Escaneo ultrarrápido de sysfs (< 1 ms)
    for h in sorted(glob.glob("/dev/hidraw*")):
        uevent_path = f"/sys/class/hidraw/{os.path.basename(h)}/device/uevent"
        if not os.path.exists(uevent_path):
            continue

        try:
            with open(uevent_path, "r") as f:
                content = f.read()
        except Exception:
            continue

        packet = None
        dev_name = None

        # POP Mouse (B030) - Feature CHANGE_HOST en índice 0x0A
        if "046D:0000B030" in content or "Logi POP Mouse" in content:
            dev_name = "Logi POP Mouse"
            packet = bytes([0x11, 0xFF, 0x0A, 0x18, target_host_index]) + (b"\x00" * 15)

        # POP Keys (B365) - Feature CHANGE_HOST en índice 0x09
        elif "046D:0000B365" in content or "Logi POP Keys" in content:
            dev_name = "Logi POP Keys"
            packet = bytes([0x11, 0xFF, 0x09, 0x18, target_host_index]) + (b"\x00" * 15)

        if packet and dev_name:
            try:
                fd = os.open(h, os.O_RDWR | os.O_NONBLOCK)
                os.write(fd, packet)
                os.close(fd)
                print(f"⚡ {dev_name} conmutado al Canal {target_host_index + 1} ({h})")
                devices_switched += 1
            except Exception as e:
                print(f"⚠️ Error escribiendo a {dev_name} en {h}: {e}")

    return devices_switched > 0

def fallback_solaar(target_host_index: int):
    """Fallback utilizando la librería de Solaar en caso de no hallar los descriptores directos."""
    sys.path.insert(0, "/usr/share/solaar/lib")
    try:
        from logitech_receiver import base, device, settings_templates
        for dev_info in base.receivers_and_devices():
            if dev_info.isDevice:
                d = device.create_device(base, dev_info)
                if d and d.features and settings_templates._F.CHANGE_HOST in d.features:
                    d.feature_request(settings_templates._F.CHANGE_HOST, 0x10, target_host_index, no_reply=True)
                    print(f"🔄 (Fallback) {d.name} conmutado al Canal {target_host_index + 1}")
    except Exception as e:
        print(f"❌ Error en fallback: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: ./switch.py <1|2|3>")
        sys.exit(1)

    channel = int(sys.argv[1])
    if channel not in (1, 2, 3):
        print("Canal inválido. Use 1, 2 o 3.")
        sys.exit(1)

    idx = channel - 1

    # Intentar conmutación directa ultrarrápida (< 5ms)
    if not fast_switch(idx):
        fallback_solaar(idx)
