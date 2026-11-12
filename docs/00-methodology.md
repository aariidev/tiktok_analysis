# 00 — Metodología

## Resumen

Este documento describe las herramientas, versiones y el proceso usado para extraer y analizar el binario de TikTok para iOS.

## App analizada

| Campo | Valor |
|---|---|
| **Nombre** | TikTok — Videos, Shop & LIVE |
| **Bundle ID** | `com.zhiliaoapp.musically` |
| **Versión** | 47.7.0 |
| **Build** | 477034 |
| **Archivo IPA** | `TikTok_47.7_TTKillerPlus_2.4.ipa` (482 MB) |
| **Descifrado por** | @FastDecryptBot (TTKiller Plus v2.4) |
| **Fecha de extracción** | 2026-11-12 |
| **Binario principal** | `MusicallyCore.framework/MusicallyCore` (866 MB, ARM64 Mach-O) |

## Proceso de obtención del IPA

El IPA fue proporcionado ya descifrado usando TTKiller Plus v2.4 (@FastDecryptBot). No se requirió jailbreak ni frida-ios-dump para este análisis. El binario fue extraído directamente desde el archivo IPA (que es un archivo ZIP) usando herramientas estándar de Windows.

## Herramientas usadas

| Herramienta | Versión | Propósito |
|---|---|---|
| PowerShell 5.x | Windows | Extracción del IPA y análisis de strings |
| .NET System.IO.Compression | — | Descompresión del archivo IPA |
| Strings (custom PowerShell) | — | Extracción de cadenas del binario Mach-O |
| Get-Content | — | Lectura de Info.plist y PrivacyInfo.xcprivacy |

## Enfoque de análisis

1. **Extracción del IPA:** Descompresión del archivo ZIP para obtener el bundle de la app.
2. **Análisis de Info.plist:** Lectura del archivo de configuración para identificar permisos, integraciones y capacidades.
3. **Análisis de PrivacyInfo.xcprivacy:** Lectura del manifesto de privacidad de Apple para ver qué datos declara recopilar.
4. **Extracción de strings:** Extracción de 50 millones de cadenas de texto del binario MusicallyCore (866 MB).
5. **Búsqueda de patrones:** Búsqueda sistemática de URLs, dominios, APIs de iOS, y referencias a datos sensibles.

## Limitaciones del análisis

- Análisis estático: no se ejecutó la app ni se capturó tráfico en vivo.
- Los símbolos Swift pueden estar completamente eliminados.
- El binario puede estar ofuscado.
- Sin `class-dump` (solo macOS), no se pudieron extraer headers Objective-C.
- Sin Ghidra en esta fase, no se realizó desensamblado profundo.
- Los strings de 50M se procesaron con patrones regex; algunos hallazgos pueden ser falsos positivos.
