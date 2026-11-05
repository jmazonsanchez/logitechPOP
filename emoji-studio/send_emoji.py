#!/usr/bin/env python3
"""
send_emoji.py - Disparador rápido para teclas de emojis de Logitech POP Keys
Se comunica instantáneamente con el demonio LogiPop para inyectar emojis sin retardo.
"""

import sys
import os
import socket
import subprocess
import time

# Exclusivo Linux
if not sys.platform.startswith("linux"):
    sys.exit(0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DAEMON_SCRIPT = os.path.join(SCRIPT_DIR, "daemon.py")

def get_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime_dir, f"logipop_emoji_{os.getuid()}.sock")

def ensure_daemon():
    sock_path = get_socket_path()
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_path)
        return s
    except Exception:
        pass

    # Si no está activo, iniciar demonio en segundo plano
    try:
        subprocess.Popen(
            ["python3", DAEMON_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(0.35)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_path)
        return s
    except Exception:
        return None

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    key_idx = sys.argv[1].strip()

    sock = ensure_daemon()
    if sock:
        try:
            sock.sendall(key_idx.encode("utf-8"))
        finally:
            sock.close()

if __name__ == "__main__":
    main()
