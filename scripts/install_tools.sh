#!/bin/bash
# install_tools.sh — Instala todas las herramientas necesarias para el análisis de TikTok iOS
# Ejecutar con: sudo bash install_tools.sh (o seguir las instrucciones interactivas)

set -euo pipefail

echo "=============================================="
echo "  Instalación de herramientas — TikTok iOS Analysis"
echo "  Fase: Preparación del entorno"
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

###############################################################################
# 1. Dependencias del sistema
###############################################################################
echo -e "${YELLOW}[1/5] Instalando dependencias del sistema...${NC}"
echo "  Se requiere sudo para este paso."
echo ""
echo "  Ejecuta manualmente:"
echo "  sudo apt-get update && sudo apt-get install -y cmake build-essential libxml2-dev"
echo ""
read -p "  ¿Ya instalaste las dependencias? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${RED}  → Abortando. Instala las dependencias primero.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Dependencias confirmadas${NC}"
echo ""

###############################################################################
# 2. class-dump — Extraer headers Objective-C
###############################################################################
echo -e "${YELLOW}[2/5] Compilando class-dump...${NC}"
CLASS_DUMP_DIR="/tmp/class-dump"
if [ -d "$CLASS_DUMP_DIR" ]; then
    echo "  → class-dump ya clonado en $CLASS_DUMP_DIR"
else
    git clone https://github.com/nygard/class-dump.git "$CLASS_DUMP_DIR"
fi

cd "$CLASS_DUMP_DIR"
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Instalar globalmente
sudo cp class-dump /usr/local/bin/
sudo cp class-dump-zip /usr/local/bin/ 2>/dev/null || true

if command -v class-dump &> /dev/null; then
    echo -e "${GREEN}  ✓ class-dump instalado: $(class-dump --version 2>&1 | head -1 || echo 'versión desconocida')${NC}"
else
    echo -e "${RED}  ✗ class-dump falló al instalarse${NC}"
    exit 1
fi
echo ""

###############################################################################
# 3. jtool2 — Inspección avanzada de Mach-O
###############################################################################
echo -e "${YELLOW}[3/5] Compilando jtool2 con Rust...${NC}"
source "$HOME/.cargo/env" 2>/dev/null || true

JTOOL2_DIR="/tmp/jtool2"
if [ -d "$JTOOL2_DIR" ]; then
    echo "  → jtool2 ya clonado en $JTOOL2_DIR"
else
    git clone https://github.com/saagarjha/jtool2.git "$JTOOL2_DIR"
fi

cd "$JTOOL2_DIR"
cargo build --release

sudo cp target/release/jtool2 /usr/local/bin/

if command -v jtool2 &> /dev/null; then
    echo -e "${GREEN}  ✓ jtool2 instalado: $(jtool2 --version 2>&1 || echo 'versión desconocida')${NC}"
else
    echo -e "${RED}  ✗ jtool2 falló al instalarse${NC}"
    exit 1
fi
echo ""

###############################################################################
# 4. Frida — Instrumentación dinámica y descifrado
###############################################################################
echo -e "${YELLOW}[4/5] Instalando Frida...${NC}"
pip3 install frida-tools --break-system-packages 2>/dev/null || pip3 install frida-tools

if command -v frida &> /dev/null; then
    echo -e "${GREEN}  ✓ Frida instalado: $(frida --version 2>&1 || echo 'versión desconocida')${NC}"
else
    echo -e "${RED}  ✗ Frida falló al instalarse${NC}"
    exit 1
fi
echo ""

###############################################################################
# 5. Verificación final
###############################################################################
echo -e "${YELLOW}[5/5] Verificando todas las herramientas...${NC}"

TOOLS=("class-dump" "jtool2" "frida" "strings" "radare2" "objdump" "file")
ALL_OK=true

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $tool"
    else
        echo -e "  ${RED}✗${NC} $tool (no encontrado)"
        ALL_OK=false
    fi
done

echo ""
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}=============================================="
    echo "  ✓ Todas las herramientas están listas"
    echo "==============================================${NC}"
    echo ""
    echo "  Siguiente paso: coloca el IPA descifrado en:"
    echo "  _work/ipa/TikTok.ipa"
    echo ""
    echo "  Luego ejecuta:"
    echo "  bash run_analysis.sh"
else
    echo -e "${RED}=============================================="
    echo "  ✗ Algunas herramientas faltan"
    echo "==============================================${NC}"
    exit 1
fi
