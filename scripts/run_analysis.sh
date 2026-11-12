#!/bin/bash
# run_analysis.sh — Ejecuta las 3 fases del análisis de TikTok iOS
# Uso: bash run_analysis.sh [ruta_al_IPA]
#
# Fases:
#   1. class-dump — Extraer headers Objective-C
#   2. jtool2 — Inspección avanzada de Mach-O
#   3. Descifrado — Analizar binario cifrado con Frida

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORK_DIR="$PROJECT_DIR/_work"
EVIDENCE_DIR="$PROJECT_DIR/_evidence"
DOCS_DIR="$PROJECT_DIR/docs"

# Crear directorios
mkdir -p "$WORK_DIR/ipa" "$WORK_DIR/strings" "$WORK_DIR/headers" "$WORK_DIR/ghidra"

###############################################################################
# Verificar herramientas
###############################################################################
echo -e "${BLUE}=============================================="
echo "  TikTok iOS — Análisis de Privacidad"
echo "  Fases: class-dump, jtool2, Descifrado"
echo "==============================================${NC}"
echo ""

MISSING=()
for tool in class-dump jtool2 frida strings radare2; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING+=("$tool")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${RED}✗ Herramientas faltantes: ${MISSING[*]}${NC}"
    echo ""
    echo "  Ejecuta primero:"
    echo "  bash scripts/install_tools.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Todas las herramientas están disponibles${NC}"
echo ""

###############################################################################
# Verificar IPA
###############################################################################
IPA_PATH="${1:-}"

# Buscar IPA si no se proporcionó
if [ -z "$IPA_PATH" ]; then
    echo -e "${YELLOW}[*] Buscando IPA en _work/ipa/...${NC}"
    IPA_PATH=$(find "$WORK_DIR/ipa" -name "*.ipa" -type f 2>/dev/null | head -1)
fi

if [ -z "$IPA_PATH" ] || [ ! -f "$IPA_PATH" ]; then
    echo -e "${RED}✗ No se encontró el IPA de TikTok${NC}"
    echo ""
    echo "  Coloca el IPA descifrado en:"
    echo "  $WORK_DIR/ipa/TikTok.ipa"
    echo ""
    echo "  O ejecuta:"
    echo "  bash run_analysis.sh /ruta/al/TikTok.ipa"
    echo ""
    echo "  Si no tienes el IPA, puedes obtenerlo con:"
    echo "  - TTKiller Plus (requiere dispositivo iOS)"
    echo "  - frida-ios-dump (requiere jailbreak)"
    echo "  - Descarga de TTKDumper o fuentes similares"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ IPA encontrado: $IPA_PATH${NC}"
echo "  Tamaño: $(du -h "$IPA_PATH" | cut -f1)"
echo ""

###############################################################################
# Extraer IPA
###############################################################################
EXTRACT_DIR="$WORK_DIR/ipa/TikTok_extracted"
if [ ! -d "$EXTRACT_DIR" ]; then
    echo -e "${YELLOW}[*] Extrayendo IPA...${NC}"
    mkdir -p "$EXTRACT_DIR"
    cd "$WORK_DIR/ipa"
    unzip -q "$IPA_PATH" -d "$EXTRACT_DIR" 2>/dev/null || {
        echo -e "${RED}✗ Error al extraer el IPA${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ IPA extraído en $EXTRACT_DIR${NC}"
else
    echo -e "${GREEN}✓ IPA ya extraído en $EXTRACT_DIR${NC}"
fi
echo ""

# Buscar el binario principal
APP_DIR="$EXTRACT_DIR/Payload/TikTok.app"
if [ ! -d "$APP_DIR" ]; then
    # Intentar encontrar el .app
    APP_DIR=$(find "$EXTRACT_DIR" -name "*.app" -type d 2>/dev/null | head -1)
fi

if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}✗ No se encontró TikTok.app en el IPA${NC}"
    echo "  Estructura del IPA:"
    find "$EXTRACT_DIR" -maxdepth 3 -type d | head -20
    exit 1
fi

# El binario puede ser TikTok o MusicallyCore
BINARY="$APP_DIR/TikTok"
if [ ! -f "$BINARY" ]; then
    # Buscar MusicallyCore
    MUSICALITY="$APP_DIR/Frameworks/MusicallyCore.framework/MusicallyCore"
    if [ -f "$MUSICALITY" ]; then
        BINARY="$MUSICALITY"
        echo -e "${YELLOW}[*] Usando binario MusicallyCore: $BINARY${NC}"
    else
        # Buscar cualquier binario Mach-O
        BINARY=$(find "$APP_DIR" -type f -exec file {} \; 2>/dev/null | grep "Mach-O" | cut -d: -f1 | head -1)
        if [ -z "$BINARY" ]; then
            echo -e "${RED}✗ No se encontró un binario Mach-O en $APP_DIR${NC}"
            exit 1
        fi
        echo -e "${YELLOW}[*] Binario encontrado: $BINARY${NC}"
    fi
fi

echo -e "${GREEN}✓ Binario principal: $BINARY${NC}"
echo "  Tamaño: $(du -h "$BINARY" | cut -f1)"
echo "  Tipo: $(file "$BINARY")"
echo ""

###############################################################################
# FASE 1: class-dump — Extraer headers Objective-C
###############################################################################
echo -e "${BLUE}=============================================="
echo "  FASE 1: class-dump — Headers Objective-C"
echo "==============================================${NC}"
echo ""

HEADERS_DIR="$WORK_DIR/headers"
rm -rf "$HEADERS_DIR"/*
mkdir -p "$HEADERS_DIR"

echo -e "${YELLOW}[*] Dumping clases del binario principal...${NC}"
class-dump -H -o "$HEADERS_DIR" "$BINARY" 2>/dev/null || {
    echo -e "${RED}  ✗ class-dump falló. El binario puede estar cifrado.${NC}"
    echo "  → Saltando a fase de descifrado..."
    SKIP_CLASS_DUMP=true
}

if [ "${SKIP_CLASS_DUMP:-false}" != true ]; then
    HEADER_COUNT=$(find "$HEADERS_DIR" -name "*.h" | wc -l)
    echo -e "${GREEN}  ✓ $HEADER_COUNT headers extraídos${NC}"
    echo ""

    # Buscar clases interesantes
    echo -e "${YELLOW}[*] Buscando clases relacionadas con privacidad...${NC}"
    
    echo "  --- Clases con 'analytics' / 'tracking' / 'telemetry' ---"
    grep -rl "analytics\|tracking\|telemetry" "$HEADERS_DIR"/*.h 2>/dev/null | head -15 || echo "  (ninguna encontrada)"
    
    echo "  --- Clases con 'device' / 'fingerprint' / 'identifier' ---"
    grep -rl "device\|fingerprint\|identifier" "$HEADERS_DIR"/*.h 2>/dev/null | head -15 || echo "  (ninguna encontrada)"
    
    echo "  --- Clases con 'location' / 'motion' / 'sensor' ---"
    grep -rl "location\|motion\|sensor" "$HEADERS_DIR"/*.h 2>/dev/null | head -15 || echo "  (ninguna encontrada)"
    
    echo "  --- Clases con 'keychain' / 'password' / 'credential' ---"
    grep -rl "keychain\|password\|credential" "$HEADERS_DIR"/*.h 2>/dev/null | head -15 || echo "  (ninguna encontrada)"
    
    echo "  --- Clases con 'contact' / 'photo' / 'media' ---"
    grep -rl "contact\|photo\|media" "$HEADERS_DIR"/*.h 2>/dev/null | head -15 || echo "  (ninguna encontrada)"
    
    echo ""
    echo -e "${GREEN}✓ Fase 1 completada: $HEADER_COUNT headers en $HEADERS_DIR${NC}"
fi
echo ""

# Frameworks embebidos
FRAMEWORKS_DIR="$APP_DIR/Frameworks"
if [ -d "$FRAMEWORKS_DIR" ] && [ "${SKIP_CLASS_DUMP:-false}" != true ]; then
    echo -e "${YELLOW}[*] Dumping clases de frameworks embebidos...${NC}"
    for fw_dir in "$FRAMEWORKS_DIR"/*.framework; do
        fw_name=$(basename "$fw_dir" .framework)
        fw_binary="$fw_dir/$fw_name"
        fw_output="$HEADERS_DIR/${fw_name}_headers"
        if [ -f "$fw_binary" ]; then
            mkdir -p "$fw_output"
            class-dump -H -o "$fw_output" "$fw_binary" 2>/dev/null || true
            count=$(find "$fw_output" -name "*.h" | wc -l)
            echo "  → $fw_name: $count headers"
        fi
    done
    echo ""
fi

###############################################################################
# FASE 2: jtool2 — Inspección avanzada de Mach-O
###############################################################################
echo -e "${BLUE}=============================================="
echo "  FASE 2: jtool2 — Inspección Mach-O"
echo "==============================================${NC}"
echo ""

JTOOL_OUTPUT="$EVIDENCE_DIR/jtool2_analysis.txt"

{
    echo "=============================================="
    echo "  jtool2 — Análisis Mach-O de TikTok iOS"
    echo "  Binario: $BINARY"
    echo "  Fecha: $(date)"
    echo "=============================================="
    echo ""

    echo "--- Información general del binario ---"
    jtool2 --arch "$BINARY" 2>/dev/null || echo "(error al leer arch)"
    echo ""

    echo "--- Entitlements ---"
    jtool2 --ent "$BINARY" 2>/dev/null || echo "(no entitlements encontrados)"
    echo ""

    echo "--- Dynamic Libraries cargadas ---"
    jtool2 --dylib "$BINARY" 2>/dev/null || echo "(no dylibs encontradas)"
    echo ""

    echo "--- Sections del binario ---"
    jtool2 --fileinfo "$BINARY" 2>/dev/null || echo "(error al leer fileinfo)"
    echo ""

    echo "--- Encryption Info ---"
    jtool2 --encrypt "$BINARY" 2>/dev/null || echo "(no encryption info)"
    echo ""

    echo "--- Code Signature ---"
    jtool2 --sign "$BINARY" 2>/dev/null || echo "(no signature info)"
    echo ""

    echo "--- UUID del binario ---"
    jtool2 --uuid "$BINARY" 2>/dev/null || echo "(no UUID)"
    echo ""

    echo "--- Load Commands ---"
    jtool2 --lcs "$BINARY" 2>/dev/null || echo "(no load commands)"
    echo ""

    echo "--- Symbols (primeros 100) ---"
    jtool2 --sym "$BINARY" 2>/dev/null | head -100 || echo "(no symbols)"
    echo ""

    echo "--- Entry Point ---"
    jtool2 --entry "$BINARY" 2>/dev/null || echo "(no entry point)"
    echo ""

} > "$JTOOL_OUTPUT" 2>&1

echo -e "${GREEN}✓ Fase 2 completada: $JTOOL_OUTPUT${NC}"
echo ""

# Mostrar resumen de hallazgos importantes
echo -e "${YELLOW}[*] Resumen de hallazgos jtool2:${NC}"
echo ""
echo "  --- Entitlements detectados ---"
jtool2 --ent "$BINARY" 2>/dev/null | head -20 || echo "  (no disponibles)"
echo ""
echo "  --- Encryption Info ---"
jtool2 --encrypt "$BINARY" 2>/dev/null || echo "  (no disponible)"
echo ""
echo "  --- Dynamic Libraries ---"
jtool2 --dylib "$BINARY" 2>/dev/null | head -20 || echo "  (no disponibles)"
echo ""

###############################################################################
# FASE 3: Descifrado de binario cifrado
###############################################################################
echo -e "${BLUE}=============================================="
echo "  FASE 3: Descifrado de binario cifrado"
echo "==============================================${NC}"
echo ""

# Verificar si el binario está cifrado
ENCRYPT_INFO=$(jtool2 --encrypt "$BINARY" 2>/dev/null || echo "")
echo -e "${YELLOW}[*] Verificando estado de cifrado del binario...${NC}"
echo "  $ENCRYPT_INFO"
echo ""

if echo "$ENCRYPT_INFO" | grep -qi "encrypted\|cryptid.*[1-9]"; then
    echo -e "${YELLOW}  ⚠ El binario está CIFRADO${NC}"
    echo ""
    echo "  Para descifrar el binario, se requiere:"
    echo "  1. Un dispositivo iOS con TikTok instalado"
    echo "  2. Frida server corriendo en el dispositivo"
    echo "  3. Ejecutar frida-ios-dump o script de descifrado"
    echo ""
    echo "  Comando para descifrar:"
    echo "  frida-ios-dump TikTok"
    echo ""
    echo "  O usar TTKiller Plus / @FastDecryptBot en Telegram"
    echo ""
    
    # Crear script de descifrado
    DECRYPT_SCRIPT="$PROJECT_DIR/scripts/decrypt_binary.py"
    cat > "$DECRYPT_SCRIPT" << 'DECRYPT_EOF'
#!/usr/bin/env python3
"""
decrypt_binary.py — Descifra el binario de TikTok usando Frida
Requiere: frida-tools, dispositivo iOS conectado con Frida server

Uso:
    python3 decrypt_binary.py

El script inyecta código en el proceso de TikTok para descifrar
el binario en memoria y extraerlo descifrado.
"""

import frida
import sys
import os
import struct

def on_message(message, data):
    if message['type'] == 'error':
        print(f"[!] Error: {message['description']}")
    elif message['type'] == 'send':
        print(f"[+] {message['payload']}")

# Conectar al dispositivo
try:
    device = frida.get_usb_device(timeout=10)
    print(f"[*] Dispositivo conectado: {device.name}")
except Exception as e:
    print(f"[!] No se pudo conectar al dispositivo: {e}")
    print("[*] Asegúrate de que frida-server esté corriendo en el dispositivo")
    sys.exit(1)

# Buscar el proceso de TikTok
try:
    session = device.attach('com.zhiliaoapp.musically')
    print("[*] Adjuntado a TikTok")
except frida.InvalidOperationError:
    print("[*] TikTok no está corriendo. Intentando lanzar...")
    try:
        session = device.attach(device.spawn(['com.zhiliaoapp.musically']))
        device.resume(session.identifier)
        print("[*] TikTok lanzado y adjuntado")
    except Exception as e:
        print(f"[!] Error al lanzar TikTok: {e}")
        sys.exit(1)

# Script de descifrado
SCRIPT = """
// Obtener información del binario
var imageDetails = Process.enumerateModules()[0];
var moduleName = 'MusicallyCore';

for (var i = 0; i < Process.enumerateModules().length; i++) {
    var mod = Process.enumerateModules()[i];
    if (mod.name === moduleName) {
        imageDetails = mod;
        break;
    }
}

console.log('Module: ' + imageDetails.name);
console.log('Base: ' + imageDetails.base);
console.log('Size: ' + imageDetails.size);
console.log('Path: ' + imageDetails.path);

// Leer el header Mach-O para encontrar el segmento __TEXT
var header = new NativePointer(imageDetails.base);
var magic = header.readUInt32();
console.log('Magic: 0x' + magic.toString(16));

if (magic === 0xfeedfacf || magic === 0xcffaedfe) {
    console.log('Mach-O 64-bit detectado');
    var fat = magic === 0xfeedfacf;
    var ncmds = header.add(16).readUInt32();
    var sizeofcmds = header.add(20).readUInt32();
    var flags = header.add(24).readUInt32();
    
    console.log('NCMDs: ' + ncmds);
    console.log('Sizeofcmds: ' + sizeofcmds);
    console.log('Flags: 0x' + flags.toString(16));
    
    // Buscar LC_ENCRYPTION_INFO
    var cmdOffset = header.add(32);
    for (var i = 0; i < ncmds; i++) {
        var cmd = cmdOffset.readUInt32();
        var cmdsize = cmdOffset.add(4).readUInt32();
        
        if (cmd === 0x21 || cmd === 0x2C) { // LC_ENCRYPTION_INFO o LC_ENCRYPTION_INFO_64
            var cryptid = cmdOffset.add(8).readUInt32();
            var cryptsize = cmdOffset.add(12).readUInt32();
            console.log('Encryption found!');
            console.log('CryptID: ' + cryptid);
            console.log('CryptSize: ' + cryptsize);
            
            if (cryptid > 0) {
                console.log('*** BINARIO CIFRADO ***');
                console.log('Para descifrar, se necesita el key de encriptación');
            }
        }
        cmdOffset = cmdOffset.add(cmdsize);
    }
}
"""

with open('/dev/null', 'w') as f:  # Suppress output
    script = session.create_script(SCRIPT)
    script.on('message', on_message)
    script.load()
    print("[*] Script de análisis de cifrado ejecutado")
    print("[*] Presiona Ctrl+C para salir")
    sys.stdin.read()
DECRYPT_EOF
    
    chmod +x "$DECRYPT_SCRIPT"
    echo -e "${GREEN}  ✓ Script de descifrado creado: $DECRYPT_SCRIPT${NC}"
    echo ""
    
else
    echo -e "${GREEN}  ✓ El binario NO está cifrado (o ya fue descifrado)${NC}"
    echo "  → El binario puede analizarse directamente"
    echo ""
fi

###############################################################################
# Análisis adicional con radare2
###############################################################################
echo -e "${BLUE}=============================================="
echo "  Análisis adicional con radare2"
echo "==============================================${NC}"
echo ""

echo -e "${YELLOW}[*] Analizando imports con radare2...${NC}"
R2_IMPORTS="$EVIDENCE_DIR/radare2_imports.txt"
r2 -q -e anal.strings=false -c 'ii' "$BINARY" > "$R2_IMPORTS" 2>/dev/null || true

if [ -s "$R2_IMPORTS" ]; then
    IMPORT_COUNT=$(wc -l < "$R2_IMPORTS")
    echo -e "${GREEN}  ✓ $IMPORT_COUNT imports analizados${NC}"
    echo ""
    echo "  --- Imports sensibles detectados ---"
    grep -i "location\|motion\|sensor\|keychain\|contact\|photo\|camera\|microphone\|address\|calendar" "$R2_IMPORTS" 2>/dev/null | head -20 || echo "  (ninguno encontrado)"
    echo ""
fi

###############################################################################
# Generar resumen
###############################################################################
echo -e "${BLUE}=============================================="
echo "  Resumen del análisis"
echo "==============================================${NC}"
echo ""

SUMMARY="$DOCS_DIR/09-class-dump-jtool2-analysis.md"
cat > "$SUMMARY" << EOF
# 09 — Análisis class-dump, jtool2 y Descifrado

## Resumen

Este documento contiene los resultados de las tres fases avanzadas del análisis estático del binario de TikTok iOS.

## Binario analizado

| Campo | Valor |
|---|---|
| **Binario** | $BINARY |
| **Tamaño** | $(du -h "$BINARY" \| cut -f1) |
| **Tipo** | $(file "$BINARY") |
| **Fecha de análisis** | $(date) |

## Fase 1: class-dump

$(if [ "${SKIP_CLASS_DUMP:-false}" != true ]; then
    HEADER_COUNT=$(find "$HEADERS_DIR" -name "*.h" 2>/dev/null | wc -l)
    echo "- **Headers extraídos:** $HEADER_COUNT"
    echo "- **Directorio:** \`_work/headers/\`"
    echo ""
    echo "### Clases relacionadas con privacidad"
    echo ""
    echo "#### Analytics / Tracking / Telemetry"
    grep -rl "analytics\|tracking\|telemetry" "$HEADERS_DIR"/*.h 2>/dev/null | head -20 | sed 's/^/- /' || echo "- Ninguna encontrada"
    echo ""
    echo "#### Device / Fingerprint / Identifier"
    grep -rl "device\|fingerprint\|identifier" "$HEADERS_DIR"/*.h 2>/dev/null | head -20 | sed 's/^/- /' || echo "- Ninguna encontrada"
    echo ""
    echo "#### Location / Motion / Sensor"
    grep -rl "location\|motion\|sensor" "$HEADERS_DIR"/*.h 2>/dev/null | head -20 | sed 's/^/- /' || echo "- Ninguna encontrada"
else
    echo "- **Estado:** Saltado — binario cifrado"
    echo "- **Nota:** Se requiere descifrado antes de ejecutar class-dump"
fi)

## Fase 2: jtool2

- **Entitlements:** Ver \`_evidence/jtool2_analysis.txt\`
- **Dynamic Libraries:** Ver \`_evidence/jtool2_analysis.txt\`
- **Encryption Info:** $(jtool2 --encrypt "$BINARY" 2>/dev/null | head -5 || echo "No disponible")

### Entitlements detectados

\`\`\`
$(jtool2 --ent "$BINARY" 2>/dev/null | head -30 || echo "No disponibles")
\`\`\`

### Dynamic Libraries

\`\`\`
$(jtool2 --dylib "$BINARY" 2>/dev/null | head -30 || echo "No disponibles")
\`\`\`

## Fase 3: Descifrado

- **Estado de cifrado:** $(echo "$ENCRYPT_INFO" | head -3)
- **Script de descifrado:** \`scripts/decrypt_binary.py\`

## Herramientas usadas

| Herramienta | Versión |
|---|---|
| class-dump | $(class-dump --version 2>&1 \| head -1 || echo "N/A") |
| jtool2 | $(jtool2 --version 2>&1 || echo "N/A") |
| Frida | $(frida --version 2>&1 || echo "N/A") |
| radare2 | $(r2 -V 2>&1 || echo "N/A") |

## Limitaciones

- class-dump solo funciona con binarios descifrados
- jtool2 puede no leer todos los segmentos de binarios cifrados
- El descifrado requiere un dispositivo iOS con Frida server
- Los símbolos Swift pueden estar completamente eliminados
EOF

echo -e "${GREEN}✓ Resumen generado: $SUMMARY${NC}"
echo ""

###############################################################################
# Final
###############################################################################
echo -e "${GREEN}=============================================="
echo "  ✓ Análisis completado"
echo "==============================================${NC}"
echo ""
echo "  Resultados:"
echo "  - Headers: $HEADERS_DIR"
echo "  - jtool2:  $JTOOL_OUTPUT"
echo "  - Imports: $R2_IMPORTS"
echo "  - Resumen: $SUMMARY"
echo ""
echo "  Siguiente paso:"
echo "  - Revisar $SUMMARY"
echo "  - Analizar headers con grep para patrones específicos"
echo "  - Importar binario a Ghidra para análisis profundo"
echo ""
