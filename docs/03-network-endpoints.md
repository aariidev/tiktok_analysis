# 03 — Endpoints de Red

## Resumen

Catálogo de todos los endpoints de red encontrados en el binario MusicallyCore de TikTok v47.7.0 para iOS, organizados por dominio y propósito.

## Método

- Búsqueda de strings que coincidan con patrones de URL (`http://`, `https://`, dominios) en 50 millones de strings.
- Identificación de paths de API en strings (`/api/`, `/v1/`, `/v2/`, etc.).
- Análisis de dominios de ByteDance y terceros.

## Dominios de ByteDance / TikTok

### API principal

| Endpoint | Dominio | Propósito |
|---|---|---|
| `api-va.tiktokv.com` | Host principal en Info.plist | API principal de TikTok |
| `api.tiktokv.com` | tiktokv.com | API general |
| `api16-normal-c-alisg.tiktokv.com` | tiktokv.com | API región Asia-Pacífico |
| `api22-normal-c-useast2a.tiktokv.com` | tiktokv.com | API región EE.UU. Este |
| `/media/api/pic/afr` | api.tiktokv.com | **Reconocimiento facial / AFR** |
| `/passport/*` | tiktokv.com | Autenticación de usuario |
| `/service/*/device_register/` | tiktokv.com | **Registro de dispositivo** |
| `/service/*/app_alert_check/` | tiktokv.com | Verificación de alertas |
| `/service/*/app_alert/` | tiktokv.com | Envío de alertas |

### Analytics y telemetría

| Endpoint | Dominio | Propósito |
|---|---|---|
| `da-an-v3.tiktokv.com` | tiktokv.com | Analytics principal (dominio de tracking) |
| `da-an-v3-va.tiktokv.com` | tiktokv.com | Analytics región Virginia |
| `da-an-v3-sg.tiktokv.com` | tiktokv.com | Analytics región Singapur |
| `da-an-v3-i18n.tiktokv.com` | tiktokv.com | Analytics internacional |
| `da-an-v3.tiktokv.us` | tiktokv.us | Analytics EE.UU. |
| `da-an-v3-ttp2.tiktokv.us` | tiktokv.us | Analytics TikTok P2 |
| `da-an-v3.tiktokv.eu` | tiktokv.eu | Analytics Europa |
| `da-an-v3-ru.tiktokv.com` | tiktokv.com | Analytics Rusia |
| `ug-sg.byteoversea.com/skan/conv` | byteoversea.com | **SKAN conversion tracking** |

### Infraestructura

| Endpoint | Dominio | Propósito |
|---|---|---|
| `gecko-sg.byteoversea.com` | byteoversea.com | Motor de reglas Singapur |
| `gecko-va.byteoversea.com` | byteoversea.com | Motor de reglas Virginia |
| `starling-sg.byteoversea.com` | byteoversea.com | Servicio Starling Singapur |
| `starling-va.byteoversea.com` | byteoversea.com | Servicio Starling Virginia |
| `mon-va.byteoversea.com` | byteoversea.com | Monitoreo Virginia |
| `wj.byteoversea.com` | byteoversea.com | Servicio interno |

### Contenido y CDN

| Endpoint | Dominio | Propósito |
|---|---|---|
| `sf-teko-source.tiktokcdn.com` | tiktokcdn.com | Recursos de Teko (imágenes) |
| `sf-static.tiktokcdn.com` | tiktokcdn.com | Juegos playable estáticos |

### Webviews in-app

| Endpoint | Dominio | Propósito |
|---|---|---|
| `inapp.tiktokv.com/tpp/inapp/pns_product_poseidon/submit-report` | tiktokv.com | Reporte de privacidad |
| `feedback.tiktokv.com/feedback/offline/topic_list` | tiktokv.com | Feedback offline |

### Wallet y biometría

| Endpoint | Dominio | Propósito |
|---|---|---|
| `/wallet/v1/user/init_biometric_registration` | tiktokv.com | **Iniciar registro biométrico** |
| `/wallet/v1/user/submit_biometric_registration` | tiktokv.com | **Enviar registro biométrico** |
| `/wallet/v1/user/close_biometric` | tiktokv.com | **Desactivar biometría** |

### Comercio y partnerships

| Endpoint | Dominio | Propósito |
|---|---|---|
| `/partnership/click_attribution_report/` | tiktokv.com | Reporte de atribución de clicks |
| `/google/measurement/skan_evaluation_event_time_millis` | tiktokv.com | **Google SKAN measurement** |
| `/google/measurement/skan_evaluation_update_backoff_millis` | tiktokv.com | **Google SKAN backoff** |
| `/ios_skadnetwork_conversion_config` | tiktokv.com | Configuración SKAdNetwork |
| `/tiktok/local/alliance/get_creator_enroll_data` | tiktokv.com | Datos de inscripción de creadores |
| `oec-api.tiktokv.com/view/fe_tiktok_ecommerce_draft` | tiktokv.com | E-commerce drafts |

### Esquemas de URL personalizados

| Scheme | Propósito |
|---|---|
| `aweme://` | Deep linking interno de TikTok |
| `bytedance://` | JS Bridge para comunicación nativa |
| `nativeapp://` | Esquema de app nativa |
| `tiktok://` | URL scheme principal |

## Dominios de terceros

| Dominio | Servicio | Tipo de datos enviados |
|---|---|---|
| `developer.paypal.com/braintree` | PayPal Braintree SDK | Datos de pago |
| `tiktok-minis.us` | Apple Mini Apps manifest | Configuración de mini apps |
| `ocsp.apple.com` | Validación OCSP | Verificación de certificados |
| `crl.apple.com` | CRL de Apple | Revocación de certificados |

## Hallazgos clave

1. **Infraestructura global:** TikTok usa múltiples regiones (Virginia, Singapur, Asia-Pacífico, EE.UU. Este, Europa, Rusia) para distribuir carga y cumplir con regulaciones locales.
2. **Tracking declarado:** Los dominios `da-an-v3.*` están declarados explícitamente en PrivacyInfo.xcprivacy como dominios de tracking.
3. **SKAN + Google:** TikTok integra SKAdNetwork de Apple con Google Measurement para atribución cruzada de anuncios.
4. **Biometría en wallet:** Los endpoints de biometría están bajo `/wallet/`, sugiriendo verificación de identidad para funciones financieras.
5. **Registro de dispositivo:** El endpoint `/service/*/device_register/` indica que TikTok registra cada dispositivo en sus servidores.
6. **Código dinámico:** El manifest de `tiktok-minis.us` permite cargar código no embebido, evadiendo parcialmente la revisión de Apple.

## Evidencia

- `_work/strings/musicallycore.txt` — Strings con URLs
- `_work/strings/domains.txt` — URLs únicas extraídas
- `_evidence/Info.plist` — API_HOST y configuraciones de red
