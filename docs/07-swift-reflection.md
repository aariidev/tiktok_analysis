# 07 — Reflexión Swift y Objective-C

## Resumen

Análisis de las clases y protocolos expuestos por el runtime de Objective-C y Swift en TikTok para identificar la estructura interna de la app y las clases relacionadas con privacidad y recopilación de datos.

## Método

```bash
# Class-dump para headers Objective-C
class-dump -H TikTok.app/TikTok -o _work/headers/

# Contar clases
ls _work/headers/ | wc -l

# Buscar clases relacionadas con privacidad
grep -ril "privacy\|telemetry\|analytics\|tracking\|fingerprint\|device" _work/headers/
```

## Estadísticas

| Métrica | Valor |
|---|---|
| Total de clases Objective-C | *(por completar)* |
| Total de protocolos | *(por completar)* |
| Clases Swift detectadas | *(por completar)* |

## Clases relacionadas con privacidad

| Clase | Categoría | Métodos notables |
|---|---|---|
| *(por completar)* | | |

## Clases de networking

| Clase | Propósito | Endpoints asociados |
|---|---|---|
| *(por completar)* | | |

## Clases de almacenamiento

| Clase | Tipo de almacenamiento | Datos almacenados |
|---|---|---|
| *(por completar)* | | |

## Protocols notables

| Protocolo | Propósito |
|---|---|
| *(por completar)* | |

## Hallazgos clave

*(Resumen de lo más importante)*

## Evidencia

- `_work/headers/` — Headers generados por class-dump
- `_evidence/class_list.txt` — Lista completa de clases
