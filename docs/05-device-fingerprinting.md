# 05 — Fingerprinting del Dispositivo

## Resumen

Análisis de cómo TikTok v47.7.0 construye un identificador único (fingerprint) del dispositivo iOS, combinando múltiples fuentes de datos de hardware y software. Se encontró evidencia directa de un procesador de fingerprinting en el código fuente.

## Método

- Búsqueda de strings relacionadas con identificación del dispositivo en 50 millones de strings.
- Identificación de `fingerprint_processor.cc` como componente dedicado de fingerprinting.
- Análisis de clases de gestión de dispositivo y tokens.

## Evidencia directa de fingerprinting

| Hallazgo | Detalle | Confianza |
|---|---|---|
| **fingerprint_processor.cc** | Archivo de código fuente en el path `/Users/iOSAndroid_ttp_1_4_v_vtur/83030/full_link_sdk/client/middleware/fingerprint_processor.cc` | **Alta** |
| **TikTokCommerceImpl** | Implementación de comercio con fingerprinting integrado | **Alta** |
| **device_id** | Identificador persistente del dispositivo en logs | **Alta** |
| **TTInstallDeviceZTIManager** | Clase de gestión de tokens de dispositivo | **Alta** |
| **BDUGPushDelegateInjection** | Inyección de delegate para push tokens | **Alta** |

## Componentes del fingerprint

| Componente | Fuente | Strings encontradas | Confianza |
|---|---|---|---|
| Device ID | `device_id` en logs | `device_id:` | **Alta** |
| Push Token | APNs | `didRegisterForRemoteNotificationsWithDeviceToken` | **Alta** |
| Modelo del dispositivo | `UIDevice` | Referencias a model | **Moderada** |
| Versión de iOS | `UIDevice` | Referencias a systemVersion | **Moderada** |
| Disk Space | API del sistema | `NSPrivacyAccessedAPICategoryDiskSpace` | **Alta** |
| System Boot Time | API del sistema | `NSPrivacyAccessedAPICategorySystemBootTime` | **Alta** |
| Active Keyboards | API del sistema | `NSPrivacyAccessedAPICategoryActiveKeyboards` | **Alta** |
| File Timestamps | API del sistema | `NSPrivacyAccessedAPICategoryFileTimestamp` | **Alta** |
| UserDefaults | API del sistema | `NSPrivacyAccessedAPICategoryUserDefaults` | **Alta** |
| Acelerómetro | `CoreMotion` | `CMAccelerometerData` | **Alta** |
| Giroscopio | `CoreMotion` | `CMGyroData` | **Alta** |
| Ubicación | `CoreLocation` | `CLLocationCoordinate2D` | **Alta** |
| Heading/Brújula | `CoreLocation` | `CLHeading` | **Alta** |
| Contador de pasos | `CMPedometer` | `startPedometerUpdates` | **Alta** |
| IDFA | `ASIdentifierManager` | SKAdNetwork integration | **Alta** |

## Persistencia del fingerprint

| Mecanismo | Evidencia | Confianza |
|---|---|---|
| **Keychain** | `TTKKeychain`, `BDABKeychainStorage`, `_has_sync_to_keychain` | **Alta** |
| **UserDefaults** | `APMUserDefaults`, `_has_sync_to_userdefaults` | **Alta** |
| **SQLite cifrado** | `WCDBSQLCipherFrameworkA.framework` | **Alta** |
| **Servidor remoto** | `/service/*/device_register/` | **Alta** |

El fingerprint persiste entre reinstalaciones mediante:
1. **Keychain:** Los datos de login y device_id se almacenan en Keychain, que sobrevive a reinstalaciones.
2. **Registro remoto:** El endpoint `/service/*/device_register/` envía el fingerprint al servidor, permitiendo correlación incluso si el dispositivo se borra.
3. **Push Token:** El token de APNs es estable y puede usarse como identificador secundario.

## SKAdNetwork y atribución

| Componente | Evidencia | Confianza |
|---|---|---|
| **SKAdNetwork reporting** | `FBAEMKitSKAdNetworkReporting`, `AFSDKSKAdNetworkDataSource` | **Alta** |
| **Google Measurement** | `/google/measurement/skan_evaluation` | **Alta** |
| **Conversion tracking** | `ug-sg.byteoversea.com/skan/conv` | **Alta** |
| **Attribution managers** | `PartnershipGameSearchAttributionManager`, `PartnershipGameDetailPageAttributionManager` | **Alta** |

TikTok usa SKAdNetwork de Apple combinado con Google Measurement para atribuir instalaciones y conversiones de anuncios, creando un perfil de comportamiento del usuario a través de múltiples plataformas.

## Comparación con Android

| Componente | Android | iOS |
|---|---|---|
| Identificador publicitario | AAID | IDFA + SKAdNetwork |
| Identificador de vendor | — | IDFV |
| Android ID / Serial | Sí | Device ID personalizado |
| MAC address | Limitado | No disponible |
| Google Advertising ID | Sí | No (usado IDFA) |
| Fingerprinting de hardware | Extensivo | CoreMotion + CoreLocation + sensors |
| Persistencia | Shared Preferences + Keychain | Keychain + SQLite cifrado + servidor |

## Hallazgos clave

1. **Procesador dedicado:** `fingerprint_processor.cc` es un componente específico de fingerprinting, no una función ad-hoc.
2. **Datos de sensor como fingerprint:** CoreMotion (acelerómetro, giroscopio, altímetro) y CoreLocation se usan para crear una huella única del dispositivo.
3. **Persistencia multi-capa:** Keychain + UserDefaults + SQLite cifrado + registro remoto aseguran que el fingerprint sobreviva a reinstalaciones.
4. **Integración con Google:** SKAdNetwork + Google Measurement permite rastrear al usuario a través de ecosistemas.
5. **APIs del sistema:** TikTok declara acceso a SystemBootTime, DiskSpace, ActiveKeyboards y FileTimestamp — todas útiles para fingerprinting.

## Evidencia

- `_work/strings/musicallycore.txt` — `fingerprint_processor.cc` y referencias a device_id
- `_evidence/PrivacyInfo.xcprivacy` — APIs del sistema accedidas
- `_evidence/Info.plist` — Permisos declarados
