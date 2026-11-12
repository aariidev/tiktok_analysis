#!/bin/bash
# extract_strings.sh — Extrae strings de todos los binarios del IPA de TikTok
# Uso: ./extract_strings.sh <ruta_a_TikTok.app> <directorio_de_salida>

set -euo pipefail

APP_DIR="${1:?Uso: $0 <TikTok.app> <output_dir>}"
OUTPUT_DIR="${2:?Uso: $0 <TikTok.app> <output_dir>}"

mkdir -p "$OUTPUT_DIR"

# Binario principal
BINARY="$APP_DIR/TikTok"
if [ -f "$BINARY" ]; then
    echo "[*] Extrayendo strings del binario principal: $BINARY"
    strings -a "$BINARY" > "$OUTPUT_DIR/main.txt"
    echo "    → $(wc -l < "$OUTPUT_DIR/main.txt") strings escritas en main.txt"
else
    echo "[!] Binario principal no encontrado: $BINARY"
fi

# Frameworks embebidos
FRAMEWORKS_DIR="$APP_DIR/Frameworks"
if [ -d "$FRAMEWORKS_DIR" ]; then
    echo "[*] Extrayendo strings de frameworks embebidos..."
    for fw_dir in "$FRAMEWORKS_DIR"/*.framework; do
        fw_name=$(basename "$fw_dir" .framework)
        fw_binary="$fw_dir/$fw_name"
        if [ -f "$fw_binary" ]; then
            strings -a "$fw_binary" > "$OUTPUT_DIR/${fw_name}.txt"
            count=$(wc -l < "$OUTPUT_DIR/${fw_name}.txt")
            echo "    → $fw_name: $count strings"
        fi
    done
else
    echo "[!] Directorio de frameworks no encontrado: $FRAMEWORKS_DIR"
fi

# PlugIns (si existen)
PLUGINS_DIR="$APP_DIR/PlugIns"
if [ -d "$PLUGINS_DIR" ]; then
    echo "[*] Extrayendo strings de PlugIns..."
    for bundle in "$PLUGINS_DIR"/*.bundle; do
        bundle_name=$(basename "$bundle" .bundle)
        for binary in "$bundle"/*; do
            if file "$binary" | grep -q "Mach-O"; then
                strings -a "$binary" > "$OUTPUT_DIR/${bundle_name}_$(basename $binary).txt"
                echo "    → $bundle_name/$(basename $binary): $(wc -l < "$OUTPUT_DIR/${bundle_name}_$(basename $binary).txt") strings"
            fi
        done
    done
fi

echo "[✓] Extracción completada. Resultados en: $OUTPUT_DIR"
