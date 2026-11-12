# TikTok iOS — Privacy Analysis

> **Pregunta central:** ¿Qué datos recopila TikTok en iOS y cómo los envía a ByteDance?
> **Método:** Análisis estático del binario Mach-O de la app de TikTok para iPhone (IPA desempaquetada).
> **Estado:** ✅ Completado — TikTok v47.7.0 (build 477034)
> **Fases completadas:** Info.plist, PrivacyInfo, strings (50M), endpoints, fingerprinting, frameworks, Swift reflection, class-dump, jtool2, verificación de cifrado

---

## ¿Qué se analiza?

| Campo | Detalle |
|---|---|
| **App** | TikTok — Videos, Shop & LIVE (iOS) |
| **Bundle ID** | `com.zhiliaoapp.musically` |
| **Versión analizada** | 47.7.0 (build 477034) |
| **Fuente del IPA** | TTKiller Plus v2.4 (@FastDecryptBot) — IPA ya descifrado |
| **Método** | Análisis estático: extracción de 50M strings de MusicallyCore (866 MB), análisis de Info.plist y PrivacyInfo.xcprivacy, búsqueda de patrones de APIs sensibles, URLs, y endpoints. Sin ejecución en vivo. |

---

## Diferencias clave con el análisis de Android

| Android | iOS |
|---|---|
| APK → JADX (Java/Kotlin decompilado) | IPA → binario Mach-O cifrado → descifrado con Frida → Ghidra/Hopper |
| `.dex` files + `.so` nativos | Binario principal + frameworks embebidos (`.framework`) |
| `AndroidManifest.xml` declara permisos | `Info.plist` + entitlements declaran capacidades |
| ProGuard obfuscation | LLVM bitcode + Swift symbol stripping |
| Permisos granulares en runtime | Capability-based (Keychain, Location, etc.) |

---

## Estructura del proyecto

```
tiktok_analysis/
├── README.md                 ← este archivo
├── docs/                     ← informes de análisis (uno por tema)
│   ├── 00-methodology.md     ← herramientas, versión del IPA, proceso de extracción
│   ├── 01-info-plist-and-entitlements.md
│   ├── 02-string-analysis.md
│   ├── 03-network-endpoints.md
│   ├── 04-data-collection.md
│   ├── 05-device-fingerprinting.md
│   ├── 06-embedded-frameworks.md
│   ├── 07-swift-reflection.md
│   ├── 08-summary-and-findings.md
│   ├── 09-class-dump-jtool2-analysis.md  ← resultados de class-dump y jtool2
│   └── SETUP.md              ← guía de instalación de herramientas
├── _work/                    ← archivos intermedios de trabajo
│   ├── ipa/                  ← IPA extraído y descifrado
│   │   ├── TikTok.ipa        ← coloca el IPA aquí
│   │   ├── TikTok_extracted/ ← IPA descomprimido
│   │   └── decrypted/        ← binario descifrado con Frida
│   ├── strings/              ← salida de strings por binario
│   ├── headers/              ← headers de class-dump
│   └── ghidra/               ← proyectos de Ghidra
├── _evidence/                ← evidencia cruda (logs, dumps, capturas)
│   ├── Info.plist
│   ├── PrivacyInfo.xcprivacy
│   ├── jtool2_analysis.txt   ← resultados de jtool2
│   └── radare2_imports.txt   ← imports analizados con radare2
└── scripts/                  ← scripts de automatización
    ├── install_tools.sh      ← instala class-dump, jtool2, Frida
    ├── run_analysis.sh       ← ejecuta las 3 fases (class-dump, jtool2, descifrado)
    ├── decrypt_binary.py     ← descifra binario con Frida
    ├── extract_strings.sh
    ├── dump_classes.sh
    └── analyze_endpoints.sh
```

---

## Herramientas requeridas

### Esenciales

- **Frida + frida-ios-dump** — Extraer y descifrar el binario Mach-O del dispositivo
- **Ghidra** (NSA) — Desensamblador/decompilador para binarios ARM64
- **class-dump** — Extraer headers Objective-C del binario
- **jtool2** — Inspección avanzada de Mach-O (entitlements, dylibs, etc.)
- **otool** — Herramienta nativa de macOS para Mach-O
- **strings** — Extraer cadenas imprimibles del binario

### Opcionales

- **Hopper Disassembler** — Alternativa a Ghidra para macOS
- **radare2** — Framework de reverse engineering
- **Frida scripts** — Instrumentación dinámica (requiere jailbreak)
- **Proxy (mitmproxy / Charles)** — Captura de tráfico HTTPS (requiere jailbreak o certificate pinning bypass)

---

## Requisitos del entorno

| Requisito | Detalle |
|---|---|
| **Dispositivo iOS** | iPhone con TikTok instalado (jailbreak recomendado para análisis dinámico) |
| **macOS o Linux** | Para ejecutar Frida, class-dump, Ghidra |
| **Python 3** | Para frida-ios-dump y scripts de análisis |
| **Java 11+** | Para Ghidra |

---

## Flujo de trabajo rápido

### Opción 1: Script automático (Recomendado)

```bash
# 1. Instalar herramientas (requiere sudo)
bash scripts/install_tools.sh

# 2. Colocar el IPA descifrado en _work/ipa/TikTok.ipa

# 3. Ejecutar las 3 fases automáticamente
bash scripts/run_analysis.sh
```

### Opción 2: Paso a paso

#### Fase 1: Obtención del IPA

1. Conectar el dispositivo iOS vía USB
2. Instalar `frida-server` en el dispositivo (requiere jailbreak) o usar TrollStore
3. Ejecutar `frida-ios-dump` para extraer el IPA descifrado:
   ```bash
   pip install frida-tools
   git clone https://github.com/AloneMonkey/frida-ios-dump
   cd frida-ios-dump
   python dump.py TikTok
   ```
4. Colocar el IPA resultante en `_work/ipa/`

#### Fase 2: Extracción inicial

```bash
# Descomprimir IPA (es un archivo ZIP)
cd _work/ipa
unzip TikTok.ipa -d TikTok_extracted

# Explorar estructura
ls -la TikTok_extracted/Payload/TikTok.app/
```

#### Fase 3: class-dump — Headers Objective-C

```bash
# Extraer headers del binario principal
class-dump -H -o _work/headers _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore

# Buscar clases relacionadas con privacidad
grep -rl "analytics\|tracking\|telemetry" _work/headers/*.h
grep -rl "device\|fingerprint\|identifier" _work/headers/*.h
grep -rl "location\|motion\|sensor" _work/headers/*.h
```

#### Fase 4: jtool2 — Inspección Mach-O

```bash
# Entitlements
jtool2 --ent _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore

# Dynamic Libraries
jtool2 --dylib _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore

# Encryption Info
jtool2 --encrypt _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore

# UUID y Load Commands
jtool2 --uuid _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore
jtool2 --lcs _work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/MusicallyCore.framework/MusicallyCore
```

#### Fase 5: Descifrado de binario cifrado

Si el binario está cifrado (cryptid > 0), se requiere un dispositivo iOS con Frida:

```bash
# Analizar cifrado y extraer binario descifrado
python3 scripts/decrypt_binary.py
```

#### Fase 6: Análisis con Ghidra

1. Abrir Ghidra
2. Importar el binario principal `MusicallyCore`
3. Importar frameworks de interés
4. Buscar referencias a:
   - URLs y endpoints de red
   - Identificadores de dispositivo (IDFV, IDFA, advertisingIdentifier)
   - Sensores (CoreMotion, CoreLocation, etc.)
   - Keychain y almacenamiento local
   - Contactos, fotos, y otros datos del usuario

#### Fase 7: Redacción de informes

Cada informe en `docs/` debe incluir:
- **Método:** Qué herramienta y qué comando se usó
- **Evidencia:** Referencia al archivo en `_evidence/` o `_work/`
- **Hallazgos:** Tablas con URLs, clases, strings encontrados
- **Confianza:** Nivel de confianza (alto/moderado/bajo)
- **Conclusión:** Qué significa para la privacidad del usuario

---

## Temas de análisis planeados

### 1. Info.plist y Entitlements
- Permisos solicitados (ubicación, cámara, micrófono, contactos, fotos)
- Capacidades de red (client/server)
- Keychain access groups
- Private API entitlements

### 2. Análisis de cadenas (strings)
- URLs hardcoded (APIs, analytics, CDN)
- Nombres de clases y métodos
- Mensajes de log y errores
- Referencias a sensores y hardware
- Keys de NSUserDefaults y Keychain

### 3. Endpoints de red
- APIs de ByteDance/ByteOversea
- Servicios de analytics y telemetría
- DNS-over-HTTP o resolución personalizada
- Third-party SDKs detectados por dominio

### 4. Recopilación de datos
- **Identificadores:** IDFV, IDFA, advertisingIdentifier, vendor identifier
- **Ubicación:** CoreLocation, GPS, Wi-Fi scanning, Cell tower
- **Dispositivo:** modelo, OS version, batería, almacenamiento, sensor de movimiento
- **Comportamiento:** tiempo de visualización, interacciones, búsqueda
- **Contactos:** acceso a la agenda de contactos
- **Fotos/Videos:** acceso a la galería

### 5. Fingerprinting del dispositivo
- Cómo TikTok construye un identificador único del dispositivo
- Uso de advertisingIdentifier vs vendor identifier
- Datos de hardware combinados (modelo + pantalla + batería + sensores)
- Persistencia del fingerprint entre reinstalaciones

### 6. Frameworks embebidos
- Lista de frameworks third-party
- SDKs de analytics (AppsFlyer, Adjust, etc.)
- SDKs de publicidad
- SDKs de video/streaming
- Bibliotecas de encriptación y seguridad

### 7. Reflexión Swift y Objective-C
- Clases expuestas vía runtime de Objective-C
- Swift classes detectadas a través de metadata
- Protocols y delegates relacionados con privacidad

### 8. Resumen y hallazgos
- Tabla resumen de todos los datos recopilados
- Comparación con Android
- Recomendaciones para minimizar exposición
- Limitaciones del análisis estático

---

## Limitaciones

- **Análisis estático:** Sin ejecutar la app, no se puede confirmar qué código realmente se ejecuta en runtime
- **Obfuscación:** Los símbolos pueden estar renombrados o eliminados
- **Cifrado de binario:** El IPA de App Store viene cifrado; se necesita descifrado con Frida
- **Swift:** A diferencia de Objective-C, Swift no expone su runtime de la misma forma
- **Sin jailbreak:** Sin jailbreak, el análisis dinámico (Frida, proxy) es muy limitado

---

## Referencias

- [akitaonrails/tiktok_analysis](https://github.com/akitaonrails/tiktok_analysis) — Análisis de TikTok Android (inspiración)
- [GhidraEnjoyr/iOS-Reverse-Engineering](https://github.com/GhidraEnjoyr/iOS-Reverse-Engineering) — Guía de RE de iOS
- [Frida-ios-dump](https://github.com/AloneMonkey/frida-ios-dump) — Extracción de IPAs descifrados
- [OWASP Mobile Top 10](https://owasp.org/www-project-mobile-top-10/) — Riesgos de seguridad móvil
- [iPhoneDevWiki](http://www.iphonedevwiki.com/) — Documentación de desarrollo iOS

---

## Licencia

Este proyecto es para investigación educativa y de seguridad. No está afiliado con ByteDance o TikTok.
