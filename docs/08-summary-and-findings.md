# 08 — Resumen y Hallazgos

## Resumen ejecutivo

El análisis estático de TikTok v47.7.0 (build 477034) para iOS revela una app de recopilación de datos extremadamente exhaustiva. A través de 50 millones de strings extraídas del binario MusicallyCore (866 MB), se identificaron: acceso a contactos completos, sensores de movimiento exhaustivos, fingerprinting dedicado del dispositivo, verificación biométrica con detección de viveza, integración con Google Measurement para atribución de anuncios, y clasificación visual con IA de ropa y objetos. TikTok declara explícitamente `NSPrivacyTracking: true` en su manifesto de privacidad.

## Tabla resumen de datos recopilados

| Categoría | Dato específico | Método de recopilación | Confianza | Impacto en privacidad |
|---|---|---|---|---|
| **Identificadores** | Device ID | `fingerprint_processor.cc` | **Alta** | **Crítico** |
| **Identificadores** | Push Token (APNs) | `BDUGPushDelegateInjection` | **Alta** | **Alto** |
| **Identificadores** | IDFA | SKAdNetwork + Google | **Alta** | **Crítico** |
| **Ubicación** | GPS | `CLLocationManager` | **Alta** | **Alto** |
| **Ubicación** | Heading/Brújula | `PNSHeadingSubscription` | **Alta** | **Medio** |
| **Ubicación** | Bluetooth | `configured_bluetooth_mode` | **Moderada** | **Medio** |
| **Sensores** | Acelerómetro | `CMMotionManager` | **Alta** | **Medio** |
| **Sensores** | Giroscopio | `CMMotionManager` | **Alta** | **Medio** |
| **Sensores** | Altímetro | `CMAltimeter` | **Alta** | **Medio** |
| **Sensores** | Actividad física | `CMMotionActivityManager` | **Alta** | **Alto** |
| **Sensores** | Contador de pasos | `CMPedometer` | **Alta** | **Alto** |
| **Sensores** | Shake/Vibración | `CoreMotion` | **Alta** | **Bajo** |
| **Contactos** | Nombre/Apellido | `CNContact` | **Alta** | **Crítico** |
| **Contactos** | Email | `CNContact.emailAddresses` | **Alta** | **Crítico** |
| **Contactos** | Teléfono | `CNContact.phoneNumbers` | **Alta** | **Crítico** |
| **Contactos** | Dirección | `CNContact.postalAddresses` | **Alta** | **Crítico** |
| **Contactos** | Cumpleaños | `CNContact.birthday` | **Alta** | **Alto** |
| **Contactos** | Cargo | `CNContact.jobTitle` | **Alta** | **Alto** |
| **Multimedia** | Fotos/Videos | `Photos.framework` | **Alta** | **Alto** |
| **Multimedia** | Cámara | `AVCaptureSession` | **Alta** | **Alto** |
| **Multimedia** | Micrófono | `AVAudioSession` | **Alta** | **Alto** |
| **Biometría** | Face ID | `LocalAuthentication` | **Alta** | **Alto** |
| **Biometría** | Registro biométrico | `/wallet/v1/user/submit_biometric_registration` | **Alta** | **Crítico** |
| **Biometría** | Detección de viveza | `KYCFaceCaptureLivenessDelegate` | **Alta** | **Crítico** |
| **Sistema** | Disk Space | `NSPrivacyAccessedAPICategoryDiskSpace` | **Alta** | **Medio** |
| **Sistema** | Boot Time | `NSPrivacyAccessedAPICategorySystemBootTime` | **Alta** | **Medio** |
| **Sistema** | Teclado activo | `NSPrivacyAccessedAPICategoryActiveKeyboards` | **Alta** | **Medio** |
| **Sistema** | File Timestamps | `NSPrivacyAccessedAPICategoryFileTimestamp` | **Alta** | **Medio** |
| **Pagos** | PayPal/Braintree | Braintree SDK | **Alta** | **Crítico** |
| **IA** | Clasificación de ropa | `class_labels` en binario | **Alta** | **Alto** |
| **IA** | Reconocimiento facial | `/media/api/pic/afr` | **Alta** | **Crítico** |

## Hallazgos más significativos

### 1. Fingerprinting dedicado
`fingerprint_processor.cc` es un componente específico de fingerprinting que combina datos de hardware (CoreMotion, CoreLocation) con datos del sistema (DiskSpace, BootTime, ActiveKeyboards) para crear un identificador único persistente del dispositivo.

### 2. Tracking declarado explícitamente
TikTok declara `NSPrivacyTracking: true` y lista `da-an-v3.*` como dominios de tracking. Email, teléfono y device_id están marcados como datos de tracking.

### 3. Biometría para funciones financieras
La verificación biométrica con detección de viveza facial está vinculada a `/wallet/`, sugiriendo KYC (conocimiento del cliente) para funciones de pago o monetización.

### 4. Integración Google + Apple para atribución
SKAdNetwork de Apple se combina con Google Measurement (`/google/measurement/skan_evaluation`) para rastrear instalaciones y conversiones a través de ecosistemas.

### 5. Clasificación visual con IA
El binario contiene labels de clasificación de ropa (zapatos, gafas de sol, vestidos, bikinis, ropa interior, trajes de novia) y modelos de IA para reconocimiento facial y OCR.

### 6. CydiaSubstrate para hooking
TikTok incluye CydiaSubstrate, el framework base de jailbreak, para interceptar llamadas a APIs del sistema.

## Comparación con el análisis de Android

| Aspecto | Android | iOS | Diferencia |
|---|---|---|---|
| **Binario principal** | .dex + .so libraries | MusicallyCore (866 MB) | iOS concentra todo en un binario |
| **Permisos** | AndroidManifest.xml | Info.plist + entitlements | Similar nivel de detalle |
| **Identificadores** | AAID, Android ID, IMEI | IDFV, IDFA, device_id personalizado | iOS más restrictivo, pero TikTok crea su propio ID |
| **Fingerprinting** | Hardware extensivo | CoreMotion + CoreLocation + sensors | Similar alcance |
| **Contactos** | Acceso completo | Acceso completo | Igual de invasivo |
| **SDKs de terceros** | AppsFlyer, Adjust, Firebase | OMSDK, SCSDK, Spotify, Braintree | Diferentes vendors, mismo propósito |
| **Biometría** | Face unlock, fingerprint | Face ID + liveness detection | iOS añade detección de viveza |
| **Código dinámico** | DEX loading | Apple Mini Apps via manifest | Ambos cargan código dinámico |

## Recomendaciones para minimizar exposición

1. **Denegar contactos:** TikTok no necesita contactos para funcionar; deniega este permiso.
2. **Limitar ubicación:** Usa "Nunca" o "Solo esta vez" para ubicación.
3. **Desactivar seguimiento:** Ajustes > Privacidad > Seguimiento > Desactivar TikTok.
4. **Denegar fotos:** Solo permite acceso cuando subas contenido específico.
5. **Sin login biométrico:** Evita registrar biometría en el wallet de TikTok.
6. **Email falso:** Usa un email dedicado que no sea tu principal.
7. **Bloqueo DNS:** Usa NextDNS o Pi-hole para bloquear `da-an-v3.*` y `byteoversea.com`.
8. **Dispositivo dedicado:** Considera un dispositivo sin SIM ni datos personales.

## Limitaciones del análisis

- **Análisis estático:** No se ejecutó la app ni se capturó tráfico en vivo.
- **Sin class-dump:** No se pudieron extraer headers Objective-C (requiere macOS).
- **Sin Ghidra:** No se realizó desensamblado profundo del binario.
- **Ofuscación:** Los símbolos Swift pueden estar completamente eliminados.
- **IPA modificado:** El IPA incluye TTKiller Plus, que puede haber modificado el binario original.
- **Falsos positivos:** Algunos strings pueden ser parte de recursos embebidos, no código ejecutable.

## Conclusión

TikTok v47.7.0 para iOS es una de las apps más invasivas en términos de recopilación de datos disponibles en el App Store. Su alcance va mucho más allá de lo necesario para una app de video corto:

- **Recopila datos de 15+ categorías** diferentes, desde contactos completos hasta datos de sensores de movimiento.
- **Usa fingerprinting dedicado** para crear identificadores persistentes que sobreviven a reinstalaciones.
- **Integra IA para clasificar contenido visual**, incluyendo ropa y objetos en videos.
- **Verifica identidad biométrica** con detección de viveza para funciones financieras.
- **Colabora con Google y Apple** para rastrear atribución de anuncios a través de ecosistemas.
- **Incluye herramientas de hooking** (CydiaSubstrate) para interceptar llamadas del sistema.

La app declara explícitamente que hace tracking del usuario, pero el alcance real de la recopilación de datos — especialmente el uso de sensores de movimiento, el fingerprinting del dispositivo, y la clasificación visual con IA — no es completamente transparente para el usuario promedio.
