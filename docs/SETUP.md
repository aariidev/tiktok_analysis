# SETUP — Guía de Instalación

Esta guía te lleva paso a paso a instalar todas las herramientas necesarias para completar las 3 fases del análisis de TikTok iOS: **class-dump**, **jtool2** y **descifrado de binario**.

## Requisitos previos

- **Kali Linux** (o cualquier distro Linux basada en Debian)
- **Acceso a sudo** para instalar paquetes del sistema
- **Conexión a internet** para descargar herramientas
- **El IPA de TikTok descifrado** (ver sección "Obtener el IPA")

---

## Paso 1: Instalar dependencias del sistema

```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential libxml2-dev unzip
```

Esto instala:
- `cmake` — Sistema de compilación para class-dump
- `build-essential` — GCC, Make y herramientas de compilación
- `libxml2-dev` — Librerías XML para analizar Info.plist

---

## Paso 2: Instalar Rust (para jtool2)

Si aún no tienes Rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
```

Verificar:
```bash
rustc --version
cargo --version
```

---

## Paso 3: Instalar class-dump

class-dump extrae los headers Objective-C del binario Mach-O, revelando las clases, métodos y propiedades de la app.

```bash
# Clonar el repositorio
git clone https://github.com/nygard/class-dump.git /tmp/class-dump
cd /tmp/class-dump

# Compilar
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Instalar globalmente
sudo cp class-dump /usr/local/bin/
sudo cp class-dump-zip /usr/local/bin/ 2>/dev/null || true
```

Verificar:
```bash
class-dump --version
```

---

## Paso 4: Instalar jtool2

jtool2 es una herramienta de inspección avanzada de binarios Mach-O que revela entitlements, dylibs, cifrado, firmas y más.

```bash
# Clonar el repositorio
git clone https://github.com/saagarjha/jtool2.git /tmp/jtool2
cd /tmp/jtool2

# Compilar con Rust
source "$HOME/.cargo/env"
cargo build --release

# Instalar globalmente
sudo cp target/release/jtool2 /usr/local/bin/
```

Verificar:
```bash
jtool2 --version
```

---

## Paso 5: Instalar Frida

Frida es un framework de instrumentación dinámica usado para descifrar binarios cifrados en iOS.

```bash
# Instalar frida-tools con pip
pip3 install frida-tools --break-system-packages 2>/dev/null || pip3 install frida-tools
```

Verificar:
```bash
frida --version
```

### Frida server en el dispositivo iOS

Para usar Frida con un dispositivo iOS, necesitas `frida-server` corriendo en el dispositivo:

1. **Descargar** la versión correcta desde https://github.com/frida/frida/releases
   - Elige `frida-ios-arm64.xz` para dispositivos modernos
2. **Copiar al dispositivo**:
   ```bash
   scp frida-server root@<IP_DEL_IPHONE>:/tmp/
   ```
3. **Ejecutar en el dispositivo**:
   ```bash
   ssh root@<IP_DEL_IPHONE>
   chmod +x /tmp/frida-server
   /tmp/frida-server &
   ```

> **Nota:** frida-server requiere jailbreak o TrollStore para ejecutarse persistentemente.

---

## Paso 6: Obtener el IPA de TikTok

Necesitas el archivo IPA de TikTok **descifrado** para analizar el binario MusicallyCore.

### Opción A: TTKiller Plus (Recomendado)

TTKiller Plus es una herramienta que extrae y descifra el IPA directamente desde un dispositivo iOS sin jailbreak.

1. Busca "TTKiller Plus" en Twitter/X
2. Sigue las instrucciones del desarrollador
3. El IPA resultante (~482 MB) se coloca en `_work/ipa/TikTok.ipa`

### Opción B: frida-ios-dump (Requiere jailbreak)

```bash
git clone https://github.com/AloneMonkey/frida-ios-dump
cd frida-ios-dump
pip3 install -r requirements.txt
python3 dump.py TikTok
```

### Opción C: @FastDecryptBot en Telegram

Si tienes acceso a un bot de descifrado en Telegram, puedes usarlo para obtener el IPA descifrado.

---

## Paso 7: Colocar el IPA en el proyecto

```bash
# Copia el IPA descifrado al directorio de trabajo
cp /ruta/al/TikTok.ipa /home/kali/Documents/tiktok_analysis/_work/ipa/TikTok.ipa
```

---

## Paso 8: Ejecutar el análisis

Una vez que tengas las herramientas instaladas y el IPA en su lugar:

```bash
cd /home/kali/Documents/tiktok_analysis
bash scripts/run_analysis.sh
```

El script ejecutará automáticamente las 3 fases:

1. **class-dump** — Extrae headers Objective-C de MusicallyCore y frameworks
2. **jtool2** — Inspecciona el binario Mach-O (entitlements, dylibs, cifrado)
3. **Descifrado** — Verifica si el binario está cifrado y proporciona herramientas para descifrarlo

---

## Verificación final

Ejecuta este comando para verificar que todo está instalado:

```bash
for tool in class-dump jtool2 frida strings radare2; do
    if command -v "$tool" &> /dev/null; then
        echo "✓ $tool"
    else
        echo "✗ $tool (falta)"
    fi
done
```

Todas las herramientas deben mostrar ✓.

---

## Estructura de resultados

Después de ejecutar el análisis, los resultados estarán en:

```
_work/
├── ipa/
│   ├── TikTok.ipa                    ← IPA original
│   ├── TikTok_extracted/             ← IPA descomprimido
│   └── decrypted/                    ← Binario descifrado (si aplica)
├── headers/                          ← Headers de class-dump
│   ├── MusicallyCore_*.h             ← Headers del binario principal
│   └── *_headers/                    ← Headers de frameworks
├── strings/                          ← Strings extraídos
└── ghidra/                           ← Proyectos de Ghidra

_evidence/
├── jtool2_analysis.txt               ← Resultados de jtool2
├── radare2_imports.txt               ← Imports analizados con radare2
├── Info.plist                        ← Configuración de la app
└── PrivacyInfo.xcprivacy             ← Manifesto de privacidad

docs/
└── 09-class-dump-jtool2-analysis.md  ← Resumen del análisis
```

---

## Solución de problemas

### class-dump falla con "bad magic"

El binario está cifrado. Necesitas descifrarlo primero con Frida o usar un IPA ya descifrado.

### jtool2 no encuentra el binario

Asegúrate de que el IPA esté extraído correctamente:
```bash
ls -la _work/ipa/TikTok_extracted/Payload/TikTok.app/
```

### Frida no conecta al dispositivo

1. Verifica que frida-server esté corriendo en el dispositivo
2. Conecta el dispositivo vía USB
3. Ejecuta `frida-ps -U` para listar procesos

### El IPA no se extrae

El IPA es un archivo ZIP. Verifica que esté intacto:
```bash
unzip -t _work/ipa/TikTok.ipa
```
