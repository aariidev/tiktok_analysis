# TikTok iOS — Privacy Analysis

> **Pregunta central:** ¿Qué datos recopila TikTok en iOS y cómo los envía a ByteDance?
> **Método:** Análisis estático del binario Mach-O de la app de TikTok para iPhone (IPA desempaquetada).
> **Estado:** ✅ Análisis completado — TikTok v47.7.0 (build 477034)

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
tiktok_nomeespiesquetedoy/
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
│   └── 08-summary-and-findings.md
├── _work/                    ← archivos intermedios de trabajo
│   ├── ipa/                  ← IPA extraído y descifrado
│   ├── strings/              ← salida de strings por binario
│   ├── headers/              ← headers de class-dump
│   └── ghidra/               ← proyectos de Ghidra
├── _evidence/                ← evidencia cruda (logs, dumps, capturas)
└── scripts/                  ← scripts de automatización
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

## Flujo de trabajo

### Fase 1: Obtención del IPA

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

### Fase 2: Extracción inicial

```bash
# Descomprimir IPA (es un archivo ZIP)
cd _work/ipa
unzip TikTok.ipa -d TikTok_extracted

# Explorar estructura
ls -la TikTok_extracted/Payload/TikTok.app/
```

### Fase 3: Análisis estático

```bash
# Strings en el binario principal
strings TikTok_extracted/Payload/TikTok.app/TikTok > _work/strings/main.txt

# Strings en frameworks embebidos
for fw in TikTok_extracted/Payload/TikTok.app/Frameworks/*.framework/*; do
    strings "$fw" > "_work/strings/$(basename $fw).txt"
done

# Class-dump para headers Objective-C
class-dump -h _work/headers -f TikTok_extracted/Payload/TikTok.app/TikTok

# Entitlements
jtool2 --ent TikTok_extracted/Payload/TikTok.app/TikTok

# Info.plist
cat TikTok_extracted/Payload/TikTok.app/Info.plist
```

### Fase 4: Análisis con Ghidra

1. Abrir Ghidra
2. Importar el binario principal `TikTok`
3. Importar frameworks de interés
4. Buscar referencias a:
   - URLs y endpoints de red
   - Identificadores de dispositivo (IDFV, IDFA, advertisingIdentifier)
   - Sensores (CoreMotion, CoreLocation, etc.)
   - Keychain y almacenamiento local
   - Contactos, fotos, y otros datos del usuario

### Fase 5: Redacción de informes

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
