# 02 — Análisis de Cadenas (Strings)

## Resumen

Análisis de las 50 millones de cadenas de texto embebidas en el binario MusicallyCore (866 MB) de TikTok v47.7.0 para identificar URLs, nombres de clases, mensajes de log, keys de almacenamiento y referencias a APIs del sistema.

## Método

```powershell
# Extracción de strings del binario MusicallyCore (866 MB)
# Usando PowerShell con System.IO.File y patrón de separación por no-ASCII
$bytes = [System.IO.File]::ReadAllBytes($binPath)
$strings = [System.Text.Encoding]::ASCII.GetString($bytes) -split '[\x00-\x08\x0E-\x1F\x7F-\xFF]+'
# Resultado: 50,048,655 strings (longitud mínima 4 caracteres)
```

## Estadísticas

| Binario | Total de strings | Tamaño del binario |
|---|---|---|
| MusicallyCore (principal) | 50,048,655 | 866 MB |
| TikTok (stub) | 389 | 77 KB |

**Nota:** El binario principal `TikTok` es un stub de 77 KB. Todo el código real reside en `MusicallyCore.framework/MusicallyCore` (866 MB).

## URLs encontradas

### Dominios de ByteDance

| Dominio | Propósito inferido |
|---|---|
| `*.tiktokv.com` | API principal, analytics, webviews in-app |
| `api.tiktokv.com` | Endpoint API principal |
| `api16-normal-c-alisg.tiktokv.com` | API región Asia-Pacífico |
| `api22-normal-c-useast2a.tiktokv.com` | API región EE.UU. Este |
| `inapp.tiktokv.com` | Webviews in-app (privacidad, feedback) |
| `feedback.tiktokv.com` | Sistema de feedback |
| `da-an-v3.tiktokv.com` | Analytics/telemetría (dominio de tracking declarado) |
| `sf-teko-source.tiktokcdn.com` | CDN de recursos (imágenes de fondo) |
| `sf-static.tiktokcdn.com` | CDN de juegos playable |
| `*.byteoversea.com` | Infraestructura ByteDance internacional |
| `gecko-sg.byteoversea.com` | Gecko (motor de reglas) Singapur |
| `gecko-va.byteoversea.com` | Gecko (motor de reglas) Virginia |
| `starling-sg.byteoversea.com` | Starling servicio Singapur |
| `starling-va.byteoversea.com` | Starling servicio Virginia |
| `mon-va.byteoversea.com` | Monitoreo Virginia |
| `wj.byteoversea.com` | Servicio interno |
| `ug-sg.byteoversea.com/skan/conv` | **SKAN conversion tracking** |

### Dominios de terceros

| Dominio | SDK / Servicio | Propósito |
|---|---|---|
| `developer.paypal.com/braintree` | PayPal Braintree SDK v6 | Pagos en-commerce |
| `developer.apple.com` | Certificados OCSP/CRL | Validación de certificados TLS |
| `tiktok-minis.us` | Apple Mini Apps | Código dinámico no embebido |

## Referencias a APIs de iOS sensibles

| API / Framework | Strings encontradas | Confianza |
|---|---|---|
| **CoreLocation** | `CLLocation`, `CLLocationManager`, `CLLocationCoordinate2D`, `PNSHeadingSubscription` | **Alta** |
| **CoreMotion** | `CMMotionManager`, `CMAccelerometerData`, `CMDeviceMotion`, `CMGyroData`, `CMAltimeter`, `CMMotionActivityManager` | **Alta** |
| **Contacts** | `CNContact`, `CNContactStore`, `givenName`, `familyName`, `emailAddresses`, `phoneNumbers`, `postalAddresses`, `birthday` | **Alta** |
| **Photos** | `Photos.framework`, `PHPhotoLibrary`, `UIImagePickerController`, `PhotoLibraryRepository` | **Alta** |
| **LocalAuthentication** | `LocalAuthentication.framework`, `biometric`, `FaceID` | **Alta** |
| **CoreBluetooth** | `bluetooth users`, `configured_bluetooth_mode` | **Moderada** |
| **Keychain** | `SecItemAdd`, `SecItemCopyMatching`, `TTKKeychain`, `FBSDKKeychain`, `GTMKeychain`, `BDABKeychainStorage` | **Alta** |
| **UserDefaults** | `NSUserDefaults`, `userDefaults`, `APMUserDefaults`, `AFSDKRCUserDefaultsStorage` | **Alta** |
| **Push Notifications** | `didRegisterForRemoteNotificationsWithDeviceToken`, `BDUGPushDelegateInjection` | **Alta** |
| **CMPedometer** | `startPedometerUpdates`, `queryPedometerDataFromDate` | **Alta** |

## Fingerprinting y telemetría

| Hallazgo | Evidencia | Confianza |
|---|---|---|
| **Fingerprinting** | `fingerprint_processor.cc` en código fuente | **Alta** |
| **Telemetría** | `telemetry_config`, `enable_deferred_cpu_usage_collect` | **Alta** |
| **SKAdNetwork** | `SKAdNetworkReporting`, `registerAppForAdNetworkAttribution`, `/google/measurement/skan_evaluation` | **Alta** |
| **Device ID** | `device_id:` en strings de log | **Alta** |
| **Push token** | `BDUGPushDelegateInjection`, `didRegisterForRemoteNotificationsWithDeviceToken` | **Alta** |

## Reconocimiento facial y biometría

| Hallazgo | Evidencia | Confianza |
|---|---|---|
| **Anti-Face-Recognition (AFR)** | `/media/api/pic/afr` endpoint | **Alta** |
| **KYC Liveness Detection** | `KYCFaceCaptureLivenessDelegate`, `livenessCompleted with frames.count` | **Alta** |
| **Biometric registration** | `/wallet/v1/user/init_biometric_registration`, `/wallet/v1/user/submit_biometric_registration` | **Alta** |
| **Biometric close** | `/wallet/v1/user/close_biometric` | **Alta** |

## IA y clasificación visual

| Hallazgo | Evidencia | Confianza |
|---|---|---|
| **Clasificación de ropa** | `class_labels`: 98_Shoes, 155_Sunglasses, 687_miniskirt, 1972_kimono, 1098_Uniforms, 1277_Hanfu_photo, 1975_underwear, 696_Swimsuit, 2420_Wedding_dress | **Alta** |
| **Modelos de IA** | `tt_face`, `tt_face_extra`, `nodehub_c1500`, `video_frame_highlight_tt`, `nodehub_image_saliency`, `ocr_det_lite` | **Alta** |

## Keys de almacenamiento

| Key | Propósito inferido |
|---|---|
| `device_id` | Identificador único del dispositivo |
| `telemetry_config` | Configuración de telemetría |
| `enable_deferred_cpu_usage_collect` | Recolección de uso de CPU |
| `__isSKAdNetworkReportEnabled` | Estado de reporte SKAdNetwork |
| `_has_sync_to_keychain` | Sincronización con Keychain |
| `_has_sync_to_userdefaults` | Sincronización con UserDefaults |

## Clases notables

| Clase | Propósito inferido |
|---|---|
| `BDUGPushDelegateInjection` | Inyección de delegate para push notifications |
| `TTInstallDeviceZTIManager` | Gestión de tokens de dispositivo |
| `FBAEMKitSKAdNetworkReporting` | Reporte SKAdNetwork de Facebook |
| `AFSDKSKAdNetworkDataSource` | DataSource de SKAdNetwork de AppsFlyer |
| `KYCFaceCaptureLivenessDelegate` | Delegate de detección de viveza para KYC |
| `PNSHeadingSubscription` | Suscripción a heading/brújula de ubicación |
| `TikTokCommerceImpl` | Implementación de comercio con fingerprinting |

## Evidencia

- `_work/strings/musicallycore.txt` — 50 millones de strings del binario principal
- `_work/strings/main.txt` — 389 strings del stub TikTok
- `_work/strings/omSDK.txt` — 5,749 strings de OMSDK_Bytedance1
- `_work/strings/domains.txt` — URLs únicas extraídas
