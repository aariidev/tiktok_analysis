# 04 — Recopilación de Datos

## Resumen

Inventario completo de los datos personales y del dispositivo que TikTok v47.7.0 puede recopilar en iOS, basado en el análisis estático del binario MusicallyCore y el manifesto PrivacyInfo.xcprivacy.

## Identificadores del dispositivo

| Identificador | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| Device ID | `device_id` en logs | `device_id:` | **Alta** |
| Push Token | `didRegisterForRemoteNotificationsWithDeviceToken` | `BDUGPushDelegateInjection` | **Alta** |
| IDFV (Identifier for Vendors) | `UIDevice` | Referencias a vendor | **Moderada** |
| IDFA (Advertising Identifier) | `ASIdentifierManager` | SKAdNetwork integration | **Alta** |
| Modelo del dispositivo | `UIDevice` | Referencias a model | **Moderada** |
| Versión de iOS | `UIDevice` | Referencias a systemVersion | **Moderada** |

## Ubicación

| Tipo | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| GPS / CoreLocation | `CLLocationManager` | `CLLocation`, `CLLocationCoordinate2D` | **Alta** |
| Heading / Brújula | `CLLocationManager` | `PNSHeadingSubscription`, `CLHeading` | **Alta** |
| Bluetooth | `CoreBluetooth` | `bluetooth users`, `configured_bluetooth_mode` | **Moderada** |

## Sensores y hardware

| Sensor | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| Acelerómetro | `CMMotionManager` | `startAccelerometerUpdates`, `CMAccelerometerData` | **Alta** |
| Giroscopio | `CMMotionManager` | `startGyroUpdates`, `CMGyroData` | **Alta** |
| Device Motion | `CMMotionManager` | `startDeviceMotionUpdates`, `CMDeviceMotion` | **Alta** |
| Altímetro | `CMAltimeter` | `startAbsoluteAltitudeUpdates`, `startRelativeAltitudeUpdates` | **Alta** |
| Actividad física | `CMMotionActivityManager` | `startActivityUpdates`, `queryActivityStartingFromDate` | **Alta** |
| Contador de pasos | `CMPedometer` | `startPedometerUpdates`, `queryPedometerDataFromDate` | **Alta** |
| Shake / Vibración | `CoreMotion` | `CMCCoreMotionShakeBaseConfigProtocol` | **Alta** |

## Datos del usuario

### Contactos

| Dato | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| Nombre | `CNContact.givenName` | `-[CNContact givenName]` | **Alta** |
| Apellido | `CNContact.familyName` | `-[CNContact familyName]` | **Alta** |
| Email | `CNContact.emailAddresses` | `-[CNContact emailAddresses]` | **Alta** |
| Teléfono | `CNContact.phoneNumbers` | `-[CNContact phoneNumbers]` | **Alta** |
| Dirección | `CNContact.postalAddresses` | `-[CNContact postalAddresses]` | **Alta** |
| Cumpleaños | `CNContact.birthday` | `-[CNContact birthday]` | **Alta** |
| Cargo | `CNContact.jobTitle` | `-[CNContact jobTitle]` | **Alta** |
| Foto de contacto | `CNContact.imageData` | `CNContactStore` | **Alta** |

### Fotos y videos

| Dato | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| Biblioteca de fotos | `Photos.framework` | `PHPhotoLibrary`, `PhotoLibraryRepository` | **Alta** |
| Selector de imágenes | `UIImagePickerController` | `UIImagePickerController`, `GCKUIImagePicker` | **Alta** |

### Biometría

| Dato | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| Face ID | `LocalAuthentication` | `LocalAuthentication.framework`, `biometric` | **Alta** |
| Registro biométrico | Endpoint REST | `/wallet/v1/user/init_biometric_registration` | **Alta** |
| Detección de viveza | KYC | `KYCFaceCaptureLivenessDelegate`, `livenessCompleted` | **Alta** |

### Datos de pago

| Dato | API usada | Strings encontradas | Confianza |
|---|---|---|---|
| PayPal/Braintree | Braintree SDK | `developer.paypal.com/braintree/docs` | **Alta** |

## Recopilación declarada en PrivacyInfo.xcprivacy

Según el manifesto de privacidad de Apple, TikTok declara:

| Dato | Vinculado a usuario | Tracking | Propósito |
|---|---|---|---|
| Nombre | Sí | No | Funcionalidad, analytics |
| Email | Sí | **Sí** | Funcionalidad, analytics |
| Teléfono | Sí | **Sí** | Funcionalidad, analytics |
| ID de dispositivo | Sí | **Sí** | Funcionalidad, analytics |
| Datos de contacto | Sí | No | Funcionalidad |
| Fotos/Videos | Sí | No | Funcionalidad |
| Datos de ubicación | Sí | No | Funcionalidad, analytics |
| Datos de sensor | Sí | No | Funcionalidad |
| Datos de pago | Sí | No | Funcionalidad |

**NSPrivacyTracking: true** — TikTok admite explícitamente hacer tracking del usuario.

## APIs del sistema accedidas (PrivacyInfo.xcprivacy)

| API | Razón declarada |
|---|---|
| `NSPrivacyAccessedAPICategoryUserDefaults` | CA92.1, 1C8F.1, C56D.1 |
| `NSPrivacyAccessedAPICategorySystemBootTime` | 35F9.1 |
| `NSPrivacyAccessedAPICategoryDiskSpace` | — |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | — |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | — |

## Almacenamiento local

| Tipo | Evidencia | Keys encontradas |
|---|---|---|
| **Keychain** | `TTKKeychain`, `FBSDKKeychain`, `GTMKeychain`, `BDABKeychainStorage` | `loginRecordDict`, `HLLoginRecords` |
| **UserDefaults** | `NSUserDefaults`, `APMUserDefaults`, `AFSDKRCUserDefaultsStorage` | `telemetry_config`, `device_id` |
| **SQLite cifrado** | `WCDBSQLCipherFrameworkA.framework` | Base de datos cifrada con SQLCipher |
| **Archivos** | App Groups (`group.com.zhiliaoapp.shared`) | Datos compartidos con extensions |

## Hallazgos clave

1. **Contactos completos:** TikTok accede a nombre, apellido, email, teléfono, dirección, cumpleaños y cargo de todos los contactos.
2. **Sensores exhaustivos:** Usa acelerómetro, giroscopio, altímetro, actividad física y contador de pasos — más allá de lo necesario para una app de video.
3. **Biometría para wallet:** La verificación biométrica con detección de viveza está vinculada a funciones financieras, no solo a login.
4. **Tracking declarado:** TikTok admite explícitamente tracking de email, teléfono e ID de dispositivo.
5. **Teclado activo:** Accede a la información del teclado activo (potencialmente para inferir idioma/ubicación).
6. **Tiempo de arranque:** Accede al tiempo de arranque del sistema, usado potencialmente para fingerprinting.

## Evidencia

- `_work/strings/musicallycore.txt` — Strings con referencias a APIs
- `_evidence/PrivacyInfo.xcprivacy` — Manifesto de privacidad completo
- `_evidence/Info.plist` — Permisos declarados
