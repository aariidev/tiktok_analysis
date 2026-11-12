# 01 — Info.plist y Entitlements

## Resumen

Análisis del archivo `Info.plist` y los entitlements del binario de TikTok v47.7.0 (build 477034) para identificar los permisos, capacidades y acceso a APIs privadas solicitados por la app.

## Info.plist

### Información general

| Campo | Valor |
|---|---|
| **CFBundleName** | TikTok |
| **CFBundleIdentifier** | com.zhiliaoapp.musically |
| **CFBundleVersion** | 477034 |
| **CFBundleShortVersionString** | 47.7.0 |
| **App Store ID** | 835599320 |
| **App Group** | group.com.zhiliaoapp.shared |
| **API Host** | api-va.tiktokv.com |

### Permisos solicitados (NSUsageDescriptionKeys)

| Clave en Info.plist | Permiso | Propósito declarado |
|---|---|---|
| `NSCameraUsageDescription` | Cámara | Grabar y tomar fotos de videos |
| `NSMicrophoneUsageDescription` | Micrófono | Grabar audio en videos |
| `NSContactsUsageDescription` | Contactos | Encontrar amigos |
| `NSLocationWhenInUseUsageDescription` | Ubicación (en uso) | Características basadas en ubicación |
| `NSLocationAlwaysAndWhenInUseUsageDescription` | Ubicación (siempre) | Características basadas en ubicación |
| `NSBluetoothAlwaysUsageDescription` | Bluetooth | Descubrir dispositivos cercanos |
| `NSLocalNetworkUsageDescription` | Red local | Descubrir dispositivos en la red |
| `NSPhotoLibraryUsageDescription` | Fotos | Seleccionar fotos y videos |
| `NSPhotoLibraryAddUsageDescription` | Fotos (escritura) | Guardar fotos y videos |

### Integraciones de terceros

| Servicio | Keys encontradas | Propósito |
|---|---|---|
| **Facebook** | `facebookAppID`, `AccountKitClientToken`, `AccountKitFacebookAppEventsEnabled` | Login social, analytics |
| **Google** | `GoogleSignInClientID` | Login social |
| **Twitter** | `twitterConsumerKey`, `twitterConsumerSecret` | Login social, compartir |
| **Line** | `lineChannelID` | Login social (Asia) |
| **Kakao** | `kakaoAppKey` | Login social (Corea) |
| **Spotify** | Framework `SpotifyLogin.framework` | Login social |
| **PayPal/Braintree** | Referencias en strings | Pagos en-commerce |
| **Sina Weibo** | `SCSDKCoreKit.framework`, `SCSDKCreativeKit.framework` | Login social (China) |

### URL Schemes registrados

TikTok registra múltiples URL schemes para deep linking y SSO:
- `tiktok://` — Scheme principal de la app
- Schemes de Facebook, Google, Twitter, Line, Kakao para callback de OAuth

### Modos en segundo plano

| Modo | Propósito |
|---|---|
| `fetch` | Descarga de datos en segundo plano |
| `audio` | Reproducción de audio en segundo plano |
| `remote-notification` | Notificaciones push |
| `voip` | Comunicaciones VoIP (posiblemente para LIVE) |

### Capacidades de Apple

| Capacidad | Key | Propósito |
|---|---|---|
| **App Groups** | `APP_GROUP_NAME` | Compartir datos con extensions |
| **DeviceCheck App Attest** | `com.apple.developer.devicecheck.appattest-environment` | Verificación de dispositivo |
| **Non-embedded software** | `com.apple.developer.non-embedded-software.manifest-url` | Apple Mini Apps (manifest en tiktok-minis.us) |

## Entitlements

### Archivos de entitlements encontrados

- `archived-expanded-entitlements.xcent`
- `cyan.entitlements`

### Entitlements clave

| Entitlement | Significado |
|---|---|
| `com.apple.security.application-groups` | App Groups para compartir datos |
| `com.apple.developer.devicecheck.appattest-environment` | App Attest para verificación |
| `application-identifier` | MJ797D8U6F.com.zhiliaoapp.musically |

## Hallazgos clave

1. **Acceso extensivo a hardware:** TikTok solicita cámara, micrófono, ubicación, Bluetooth, contactos, fotos y red local.
2. **Integración con 6+ redes sociales:** Facebook, Google, Twitter, Line, Kakao, Spotify para login y compartir.
3. **Modo VoIP en segundo plano:** Sugiere funcionalidad de comunicación en tiempo real, posiblemente para LIVE.
4. **Apple Mini Apps:** TikTok usa el manifest de non-embedded software para cargar código dinámico desde `tiktok-minis.us`.
5. **App Groups:** Permite compartir datos entre la app principal y sus extensions (widget, share extension, etc.).
6. **SKAdNetwork:** Configurado para atribución de anuncios de Apple con integración de Google Measurement.

## Evidencia

- `_evidence/Info.plist` — Copia completa del Info.plist extraído
- `_evidence/PrivacyInfo.xcprivacy` — Manifesto de privacidad de Apple
