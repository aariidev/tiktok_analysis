#!/bin/bash
# dump_classes.sh — Extrae headers Objective-C usando class-dump
# Uso: ./dump_classes.sh <ruta_a_TikTok.app> <directorio_de_salida>

set -euo pipefail

APP_DIR="${1:?Uso: $0 <TikTok.app> <output_dir>}"
OUTPUT_DIR="${2:?Uso: $0 <TikTok.app> <output_dir>}"

mkdir -p "$OUTPUT_DIR"

# Binario principal
BINARY="$APP_DIR/TikTok"
if [ -f "$BINARY" ]; then
    echo "[*] Dumping clases del binario principal: $BINARY"
    class-dump -H -o "$OUTPUT_DIR" "$BINARY"
    count=$(ls "$OUTPUT_DIR"/*.h 2>/dev/null | wc -l)
    echo "    → $count headers escritos en $OUTPUT_DIR"
else
    echo "[!] Binario principal no encontrado: $BINARY"
fi

# Frameworks embebidos
FRAMEWORKS_DIR="$APP_DIR/Frameworks"
if [ -d "$FRAMEWORKS_DIR" ]; then
    echo "[*] Dumping clases de frameworks embebidos..."
    for fw_dir in "$FRAMEWORKS_DIR"/*.framework; do
        fw_name=$(basename "$fw_dir" .framework)
        fw_binary="$fw_dir/$fw_name"
        fw_output="$OUTPUT_DIR/${fw_name}_headers"
        if [ -f "$fw_binary" ]; then
            mkdir -p "$fw_output"
            class-dump -H -o "$fw_output" "$fw_binary" 2>/dev/null || true
            count=$(ls "$fw_output"/*.h 2>/dev/null | wc -l)
            echo "    → $fw_name: $count headers"
        fi
    done
fi

# Buscar clases interesantes
echo ""
echo "[*] Buscando clases relacionadas con privacidad..."
echo "    --- Clases con 'analytics' / 'tracking' / 'telemetry' ---"
grep -ril "analytics\|tracking\|telemetry" "$OUTPUT_DIR"/*.h 2>/dev/null | head -20 || echo "    (ninguna encontrada)"

echo "    --- Clases con 'device' / 'fingerprint' / 'identifier' ---"
grep -ril "device\|fingerprint\|identifier" "$OUTPUT_DIR"/*.h 2>/dev/null | head -20 || echo "    (ninguna encontrada)"

echo "    --- Clases con 'location' / 'motion' / 'sensor' ---"
grep -ril "location\|motion\|sensor" "$OUTPUT_DIR"/*.h 2>/dev/null | head -20 || echo "    (ninguna encontrada)"

echo ""
echo "[✓] Dump completado. Headers en: $OUTPUT_DIR"
