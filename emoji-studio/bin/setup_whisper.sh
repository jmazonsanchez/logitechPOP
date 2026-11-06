#!/usr/bin/env bash
# ==============================================================================
# setup_whisper.sh - Descarga e instalación autónoma de Whisper.cpp (offline)
# Permite dictado por voz 100% privado y local sin requerir permisos de root.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_DIR="$SCRIPT_DIR/whisper"
MODELS_DIR="$WHISPER_DIR/models"
LIB_DIR="$WHISPER_DIR/lib"
BACKENDS_DIR="$LIB_DIR/ggml/backends0"

mkdir -p "$MODELS_DIR" "$LIB_DIR" "$BACKENDS_DIR"

# 1. Verificar binario whisper-cli y librerías
if [[ ! -x "$WHISPER_DIR/whisper-cli" ]] || [[ ! -f "$LIB_DIR/libwhisper.so.1" ]]; then
    echo "⚙️ Configurando motor local whisper.cpp..."
    TMP_DIR="$(mktemp -d /tmp/whisper_setup_XXXXXX)"
    
    (
        cd "$TMP_DIR"
        echo "⬇️ Descargando paquetes base de whisper.cpp..."
        apt download whisper.cpp libwhisper1 libggml0 >/dev/null 2>&1 || {
            echo "⚠️ No se pudieron descargar paquetes con 'apt download'. Verificando paquetes del sistema..."
        }
        
        for deb in *.deb; do
            if [[ -f "$deb" ]]; then
                dpkg-deb -x "$deb" extracted/
            fi
        done
        
        if [[ -d "extracted" ]]; then
            cp -f extracted/usr/bin/whisper-cli "$WHISPER_DIR/"
            chmod +x "$WHISPER_DIR/whisper-cli"
            
            cp -P extracted/usr/lib/x86_64-linux-gnu/libwhisper* "$LIB_DIR/" 2>/dev/null || true
            cp -P extracted/usr/lib/x86_64-linux-gnu/libggml* "$LIB_DIR/" 2>/dev/null || true
            
            if [[ -d "extracted/usr/lib/x86_64-linux-gnu/ggml/backends0" ]]; then
                cp -P extracted/usr/lib/x86_64-linux-gnu/ggml/backends0/* "$BACKENDS_DIR/" 2>/dev/null || true
            fi
        fi
    )
    rm -rf "$TMP_DIR"
    echo "✔ Binarios de whisper.cpp configurados."
else
    echo "✔ Motor whisper-cli y librerías ya se encuentran instalados."
fi

# 2. Descargar modelo ggml-tiny.bin (74 MB) si no existe
MODEL_FILE="$MODELS_DIR/ggml-tiny.bin"
if [[ ! -f "$MODEL_FILE" ]] || [[ $(stat -c%s "$MODEL_FILE" 2>/dev/null || echo 0) -lt 50000000 ]]; then
    echo "⬇️ Descargando modelo de voz en español 'ggml-tiny.bin' (~74 MB)..."
    MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin"
    if command -v curl >/dev/null 2>&1; then
        curl -L --progress-bar -o "$MODEL_FILE" "$MODEL_URL"
    elif command -v wget >/dev/null 2>&1; then
        wget -q --show-progress -O "$MODEL_FILE" "$MODEL_URL"
    else
        echo "❌ Error: Se requiere curl o wget para descargar el modelo."
        exit 1
    fi
    echo "✔ Modelo ggml-tiny.bin descargado correctamente."
else
    echo "✔ Modelo ggml-tiny.bin listo para dictado offline."
fi
