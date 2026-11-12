# 06 — Frameworks Embebidos

## Resumen

Inventario de los 18 frameworks embebidos en TikTok v47.7.0 para iOS, identificando SDKs de terceros, bibliotecas de video, criptografía y seguridad.

## Método

Listado de frameworks en `TikTok.app/Frameworks/` con análisis de tamaños y propósitos inferidos desde los nombres y strings.

## Frameworks de ByteDance

| Framework | Tamaño | Propósito inferido |
|---|---|---|
| **MusicallyCore** | 866 MB | **Binario principal** — toda la lógica de la app |
| **TTFFmpeg** | 3.2 MB | Decodificación/codec de video (FFmpeg) |
| **TTPOrbuService** | 2.3 MB | Servicio Orbuz (posiblemente P2P/streaming) |
| **OMSDK_Bytedance1** | 302 KB | Analytics/telemetría de ByteDance |
| **bytevc1enc** | 978 KB | Codificador de video VC1 |
| **libvcn** | Desconocido | Visión por computadora / reconocimiento |
| **AAAASingularity** | Desconocido | Servicio de singularidad (IA/recomendaciones) |
| **AAWEBootChecker** | Desconocido | Verificación de arranque (seguridad) |
| **AAWELaunchTracker** | Desconocido | Tracking de lanzamiento de la app |
| **WCDBSQLCipherFrameworkA** | 1.2 MB | Base de datos SQLite cifrada (WeChat WCDB + SQLCipher) |
| **crypto** | 1.6 MB | Criptografía general |
| **TTKPlus.dylib** | 810 KB | Biblioteca dinámica de TTKiller Plus (modificación de terceros) |

## SDKs de terceros detectados

| Framework | Vendor | Propósito | Datos recopilados |
|---|---|---|---|
| **SCSDKCoreKit** | Sina Weibo | Login social China | Perfil de Weibo, contactos |
| **SCSDKCreativeKit** | Sina Weibo | Contenido creativo de Weibo | Contenido compartido |
| **SpotifyLogin** | Spotify | Login social | Perfil de Spotify |
| **CydiaSubstrate** | Jay Freeman (Saurik) | Hooking/instrumentación | Permite modificar comportamiento de otras apps |
| **boringssl** | Google | Criptografía TLS/SSL | Conexiones seguras |
| **ffmpeg_dashdec** | FFmpeg | Decodificación DASH de video | Metadatos de video |

### SDK de hooking: CydiaSubstrate

**CydiaSubstrate** (387 KB) es particularmente notable:
- Es el framework base de jailbreak de iOS para hooking de métodos.
- Permite interceptar y modificar el comportamiento de cualquier método Objective-C.
- Su presencia sugiere que TikTok usa hooking para instrumentación interna o para detectar jailbreak.
- **Riesgo de privacidad:** Permite a TikTok interceptar llamadas a APIs del sistema que de otra forma serían difíciles de monitorear.

### SDK de analytics: OMSDK_Bytedance1

**OMSDK_Bytedance1** (302 KB) es el SDK de analytics de ByteDance:
- Recopila datos de uso y rendimiento.
- Se integra con los dominios `da-an-v3.*` de tracking.
- Trabaja con SKAdNetwork para atribución de anuncios.

## SDKs de video/streaming

| SDK | Vendor | Propósito |
|---|---|---|
| **TTFFmpeg** | ByteDance (basado en FFmpeg) | Decodificación de video H.264/H.265 |
| **bytevc1enc** | ByteDance | Codificación de video VC1 |
| **ffmpeg_dashdec** | FFmpeg | Decodificación de streams DASH |
| **ffmpeg_dashdec.bc** | FFmpeg | Bytecode de FFmpeg DASH |

## Bibliotecas de encriptación

| Biblioteca | Propósito |
|---|---|
| **boringssl** (710 KB) | TLS/SSL de Google — conexiones seguras a servidores |
| **crypto** (1.6 MB) | Criptografía general — hashing, cifrado de datos locales |
| **WCDBSQLCipherFrameworkA** (1.2 MB) | SQLite cifrado con SQLCipher — base de datos local protegida |

## Hallazgos clave

1. **MusicallyCore es todo:** El 99% del código está en un solo framework de 866 MB, lo que hace el análisis más difícil pero concentra toda la lógica.
2. **CydiaSubstrate embebido:** TikTok incluye un framework de jailbreak para hooking, lo que le permite interceptar llamadas del sistema.
3. **TTKiller Plus modificado:** El IPA incluye `TTKPlus.dylib` (810 KB), una modificación de terceros que probablemente deshabilita protecciones.
4. **Criptografía robusta:** Usa BoringSSL de Google + SQLCipher para proteger datos locales, lo que sugiere que almacena datos sensibles.
5. **SDKs de login social:** Weibo (China), Spotify, y los keys de Facebook/Google/Twitter en Info.plist muestran integración global.
6. **Base de datos cifrada:** WCDB (de WeChat) con SQLCipher indica almacenamiento local significativo de datos del usuario.

## Evidencia

- `_work/ipa/TikTok_extracted/Payload/TikTok.app/Frameworks/` — Frameworks extraídos
- `_work/strings/omSDK.txt` — Strings de OMSDK_Bytedance1
