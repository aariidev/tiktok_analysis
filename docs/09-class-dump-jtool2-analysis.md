# 09 — class-dump y jtool2 Analysis

## Resumen

Este documento presenta los resultados de las 3 fases faltantes del análisis de TikTok iOS:
1. **class-dump** — Extracción de clases Objective-C y Swift
2. **jtool2** — Inspección avanzada del binario Mach-O
3. **Descifrado de binario** — Verificación del estado de cifrado

> **Nota:** class-dump y jtool2 son herramientas exclusivas de macOS. Se crearon alternativas en Python que usan `strings` y parsing directo de headers Mach-O para replicar su funcionalidad en Linux.

---

## Fase 1: class-dump — Clases Objective-C

### Método

Como class-dump no funciona en Linux, se usó `strings` para extraer símbolos `_OBJC_CLASS_$_` del binario MusicallyCore, que revelan las clases Objective-C referenciadas.

```bash
strings MusicallyCore | grep -oP '_OBJC_CLASS_\$_\K[^_]+$' | sort -u
```

### Resultados

| Métrica | Valor |
|---|---|
| **Clases Objective-C encontradas** | 782 |
| **Símbolos de tracking** | 13,847 |
| **Símbolos de device info** | 586 |
| **Símbolos de fingerprinting** | 397 |

### Clases relacionadas con privacidad

#### Analytics y Tracking

| Clase | Propósito |
|---|---|
| `ATTrackingManager` | IDFA y tracking de publicidad (App Tracking Transparency) |
| `ASIdentifierManager` | Identificador publicitario (IDFA) |
| `MXMetricManager` | Métricas de rendimiento |
| `NSURLSessionTaskMetrics` | Métricas de red |
| `NSURLSessionTaskTransactionMetrics` | Métricas de transacciones de red |

#### Dispositivo y Fingerprinting

| Clase | Propósito |
|---|---|
| `UIDevice` | Modelo, sistema operativo, nombre del dispositivo |
| `ASIdentifierManager` | IDFA (advertising identifier) |
| `NSUUID` | Identificadores únicos |
| `CBUUID` | UUID de Bluetooth |
| `DCDevice` | Información del dispositivo |
| `AVCaptureDevice` | Cámara y dispositivos de captura |

#### Ubicación y Sensores

| Clase | Propósito |
|---|---|
| `CLLocation` | Coordenadas GPS |
| `CLLocationManager` | Gestión de ubicación |
| `CMAccelerometerData` | Datos del acelerómetro |
| `CMDeviceMotion` | Movimiento del dispositivo (acelerómetro + giroscopio) |
| `CMGyroData` | Datos del giroscopio |
| `CMMotionManager` | Gestión de sensores de movimiento |
| `MKUserLocation` | Ubicación en mapas |

#### Contactos y Media

| Clase | Propósito |
|---|---|
| `CNContact` | Datos de contactos |
| `CNContactStore` | Almacén de contactos |
| `CNContactFetchRequest` | Solicitud de contactos |
| `CNContactPickerViewController` | Selector de contactos |
| `PHPhotoLibrary` | Biblioteca de fotos |
| `PHLivePhoto` | Fotos en vivo |
| `AVCapturePhotoOutput` | Salida de fotos de cámara |
| `MPMediaLibrary` | Biblioteca de música |

#### Autenticación y Credenciales

| Clase | Propósito |
|---|---|
| `ACAccountCredential` | Credenciales de cuentas |
| `ASAuthorizationAppleIDCredential` | Login con Apple |
| `NSURLCredential` | Credenciales de red |
| `NSURLCredentialStorage` | Almacenamiento de credenciales |
| `PKPaymentAuthorizationController` | Autorización de pagos |

### Infraestructura de Tracking descubierta

Los símbolos Swift revelan una infraestructura masiva de tracking con **13,847 símbolos** relacionados:

- `eventTracker` / `eventTrackingService` — Rastreo de eventos
- `pageTracker` / `pageStayTracker` — Rastreo de páginas y tiempo de permanencia
- `clickTrackURLListModel` — Rastreo de clics en URLs
- `cameraPerfTracker` — Rastreo de rendimiento de cámara
- `latencyTracker` — Rastreo de latencia
- `perfTracker` / `perfTrackerService` — Rastreo de rendimiento general
- `deviceResourceTracker` — Rastreo de recursos del dispositivo
- `interactionPageStayTracker` — Rastreo de interacciones
- `chatListTracker` / `chatNoticeTracker` — Rastreo de chats
- `paymentDetailTracker` — Rastreo de pagos
- `businessTracker` — Rastreo de negocios/comercio
- `aiChatTracker` — Rastreo de chat con IA
- `beautyEventTracker` — Rastreo de eventos de belleza/filtros

### Fingerprinting de Audio/Video

Se descubrieron **397 símbolos** relacionados con fingerprinting:

- `AIGCFingerprintAlgorithmDownloader` — Descarga de algoritmos de fingerprinting AIGC
- `AIGCFingerprintExtractor` — Extracción de fingerprints AIGC
- `aigcFingerprintShouldAddInvisibleWatermarkWithPublishModel` — **Marca de agua invisible en contenido publicado**
- `AIGCFingerprintTools` — Herramientas de fingerprinting AIGC
- `aiFingerprintConfig` — Configuración de fingerprinting de IA
- `ai_fingerprint_model_download` — Descarga de modelos de fingerprinting

---

## Fase 2: jtool2 — Inspección Mach-O

### Método

Se creó un parser Python que lee los headers Mach-O directamente sin cargar el binario completo en memoria, extrayendo load commands, dylibs, segments, encryption info, y entitlements.

### Información general

| Campo | Valor |
|---|---|
| **Binario** | `MusicallyCore.framework/MusicallyCore` |
| **Tamaño** | 866.9 MB (908,989,360 bytes) |
| **Arquitectura** | arm64 |
| **Tipo** | MH_DYLIB (dynamic library) |
| **Load commands** | 189 |
| **Flags** | 0x6910085 |
| **UUID** | `28cc5534-882f-7900-2900-000010000000` |

### Estado de cifrado

| Campo | Valor |
|---|---|
| **LC_ENCRYPTION_INFO** | No encontrado |
| **Estado** | ✅ **NO CIFRADO** |

El binario fue descifrado por TTKiller Plus (@FastDecryptBot). Al no tener `LC_ENCRYPTION_INFO`, el binario está completamente accesible para análisis estático.

### Segments

| Segment | Secciones | Tamaño | Descripción |
|---|---|---|---|
| `__TEXT` | 31 | 745 MB | Código ejecutable |
| `__DATA_CONST` | 15 | 38.6 MB | Constantes |
| `__DATA` | 71 | 93.7 MB | Datos mutables |
| `__LINKEDIT` | 0 | 31.5 MB | Tabla de símbolos |

### Dynamic Libraries (116)

#### Frameworks del sistema relevantes para privacidad

| Framework | Datos recopilados |
|---|---|
| `CoreMotion.framework` | Acelerómetro, giroscopio, magnetómetro |
| `CoreLocation.framework` | GPS y ubicación |
| `CoreTelephony.framework` | Información de red celular |
| `AdSupport.framework` | IDFA (identificador publicitario) |
| `Photos.framework` | Galería de fotos |
| `PhotosUI.framework` | Selector de fotos |
| `CoreBluetooth.framework` | Bluetooth |
| `MapKit.framework` | Mapas y geolocalización |
| `Speech.framework` | Reconocimiento de voz |
| `LocalAuthentication.framework` | TouchID/FaceID |
| `NetworkExtension.framework` | Acceso a red avanzada |
| `EventKit.framework` | Calendario |
| `SafariServices.framework` | Safari/WebView |
| `CloudKit.framework` | iCloud |
| `GameController.framework` | Controladores de juego |
| `ARKit.framework` | Realidad aumentada |
| `CallKit.framework` | Llamadas VoIP |
| `PassKit.framework` | Apple Pay/Wallet |
| `Security.framework` | Keychain, certificados |
| `Social.framework` | Redes sociales |
| `Accounts.framework` | Cuentas del sistema |
| `UserNotifications.framework` | Notificaciones |
| `BackgroundTasks.framework` | Tareas en segundo plano |
| `Vision.framework` | Reconocimiento visual/ML |
| `CoreML.framework` | Machine Learning |
| `CoreSpotlight.framework` | Búsqueda Spotlight |
| `PushKit.framework` | Push notifications |

#### Librerías de terceros embebidas

| Librería | Propósito |
|---|---|
| `SpotifyLogin.framework` | Login con Spotify |
| `TTFFmpeg.framework` | Decodificación de video (FFmpeg) |
| `WCDBSQLCipherFrameworkA.framework` | Base de datos encriptada local |
| `boringssl.framework` | TLS/SSL (Google) |
| `bytevc1enc.framework` | Codificador de video |
| `crypto.framework` | Criptografía |
| `OMSDK_Bytedance1.framework` | Mide measurement SDK |
| `SCSDKCoreKit.framework` | Sina Weibo SDK |
| `SCSDKCreativeKit.framework` | Sina Weibo Creative SDK |

### Entitlements

| Entitlement | Valor | Implicación de privacidad |
|---|---|---|
| `application-identifier` | `MJ797D8U6F.com.zhiliaoapp.musically` | Identificador único de la app |
| `aps-environment` | `production` | Push notifications activas |
| `com.apple.developer.applesignin` | `Default` | Login con Apple |
| `com.apple.developer.networking.wifi-info` | ✅ | **Acceso a BSSID/SSID de Wi-Fi** |
| `com.apple.developer.networking.multicast` | ✅ | Multicast networking |
| `com.apple.developer.kernel.increased-memory-limit` | ✅ | Memoria extendida |
| `com.apple.developer.siri` | ✅ | Integración con Siri |
| `com.apple.security.application-groups` | ✅ | Shared app group container |
| `keychain-access-groups` | ✅ | **Acceso a Keychain** |
| `com.apple.developer.usernotifications.time-sensitive` | ✅ | Notificaciones prioritarias |
| `com.apple.developer.usernotifications.communication` | ✅ | Notificaciones de comunicación |
| `com.apple.developer.pass-type-identifiers` | ✅ | Apple Wallet |
| `com.apple.developer.in-app-payments` | ✅ | Pagos en app |
| `com.apple.developer.associated-domains` | Múltiples dominios tiktok.com | Universal Links |

---

## Fase 3: Descifrado de binario

### Verificación

El binario **ya está descifrado** por TTKiller Plus. No se requiere descifrado adicional con Frida.

| Verificación | Resultado |
|---|---|
| `LC_ENCRYPTION_INFO` | No presente |
| `cryptid` | 0 (no cifrado) |
| Fuente del IPA | TTKiller Plus v2.4 (@FastDecryptBot) |
| Análisis estático posible | ✅ Sí, binario completo accesible |

### Evidencia

```
No se encontró LC_ENCRYPTION_INFO en el binario
Estado: NO CIFRADO (sin comando de cifrado = binario ya descifrado)
```

---

## Hallazgos clave de privacidad

### 1. Infraestructura masiva de tracking

- **13,847 símbolos** relacionados con tracking
- Trackers para: eventos, páginas, clics, cámara, latencia, rendimiento, chats, pagos, IA, belleza, negocios
- Tracking de tiempo de permanencia en cada página (`pageStayTracker`, `interactionPageStayTracker`)

### 2. Fingerprinting avanzado

- **397 símbolos** de fingerprinting
- Fingerprinting AIGC con **marcas de agua invisibles** en contenido publicado
- Modelos de IA descargados para fingerprinting
- Fingerprinting de audio (`afp_test.wav`)

### 3. Recopilación de datos del dispositivo

- **586 símbolos** de información del dispositivo
- Modelo, nombre, tipo, almacenamiento, memoria, cámara, Bluetooth
- Uso de `UIDevice`, `AVCaptureDevice`, `CMMotionManager`

### 4. Frameworks sensibles

- **CoreMotion**: Acelerómetro, giroscopio, magnetómetro
- **CoreLocation**: GPS y ubicación
- **AdSupport**: IDFA para tracking publicitario
- **CoreTelephony**: Información de red celular
- **LocalAuthentication**: Biometría (TouchID/FaceID)
- **NetworkExtension**: Acceso avanzado a red
- **Vision + CoreML**: Reconocimiento visual y ML

### 5. Almacenamiento encriptado local

- `WCDBSQLCipherFrameworkA`: Base de datos SQLCipher encriptada
- `boringssl`: TLS/SSL para comunicaciones
- `crypto.framework`: Criptografía propia

### 6. Entitlements extensivos

- Acceso a información de Wi-Fi (BSSID/SSID)
- Keychain para almacenamiento de credenciales
- Push notifications en producción
- Integración con Siri
- Pagos en app y Apple Wallet

---

## Scripts creados

| Script | Propósito |
|---|---|
| `scripts/class_dump_linux.py` | Alternativa a class-dump usando LIEF + nm |
| `scripts/jtool2_linux.py` | Alternativa a jtool2 usando LIEF |
| `scripts/macho_inspect.py` | Parser ligero de headers Mach-O (sin cargar binario completo) |

## Evidencia

| Archivo | Contenido |
|---|---|
| `_evidence/jtool2_analysis.txt` | Resultados completos de inspección Mach-O |
| `_work/headers/objc_classes.txt` | 782 clases Objective-C |
| `_work/headers/tracking_symbols.txt` | 13,847 símbolos de tracking |
| `_work/headers/device_info_symbols.txt` | 586 símbolos de info del dispositivo |
| `_work/headers/fingerprint_symbols.txt` | 397 símbolos de fingerprinting |

---

## Limitaciones

- Sin class-dump real de macOS, no se obtuvieron los métodos y variables de cada clase
- Sin Ghidra/Hopper, no se realizó desensamblado profundo
- Los símbolos Swift están parcialmente ofuscados (nombres como `$s19TikTokUITrackerImpl...`)
- Sin jailbreak, no se pudo hacer análisis dinámico con Frida
