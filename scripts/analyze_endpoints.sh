#!/bin/bash
# analyze_endpoints.sh — Busca y categoriza endpoints de red en los strings extraídos
# Uso: ./analyze_endpoints.sh <directorio_con_strings>

set -euo pipefail

STRINGS_DIR="${1:?Uso: $0 <strings_dir>}"

if [ ! -d "$STRINGS_DIR" ]; then
    echo "[!] Directorio no encontrado: $STRINGS_DIR"
    exit 1
fi

OUTPUT_FILE="_evidence/network_endpoints.txt"
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "[*] Buscando endpoints de red en: $STRINGS_DIR"
echo ""

# Patrones de búsqueda
DOMAINS=(
    "byteoversea"
    "tiktokv"
    "tiktok.com"
    "musical.ly"
    "byteintl"
    "bytedance"
    "snssdk"
    "iesdouyin"
    "p16-tiktok"
    "bytegoofy"
)

THIRD_PARTY=(
    "appsflyer"
    "adjust"
    "firebase"
    "google"
    "facebook"
    "meta"
    "amazon"
    "aws"
    "cloudfront"
    "akamai"
    "fastly"
    "segment"
    "mixpanel"
    "amplitude"
    "onesignal"
    "branch"
    "stripe"
    "paypal"
    "venmo"
    "spotify"
)

echo "==========================================" > "$OUTPUT_FILE"
echo "  Endpoints de Red — TikTok iOS" >> "$OUTPUT_FILE"
echo "  Generado: $(date)" >> "$OUTPUT_FILE"
echo "==========================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Dominios de ByteDance
echo "--- Dominios de ByteDance/TikTok ---" >> "$OUTPUT_FILE"
for domain in "${DOMAINS[@]}"; do
    matches=$(grep -rhi "$domain" "$STRINGS_DIR"/*.txt 2>/dev/null | grep -oE 'https?://[^ "'"'"'<>]+|[^ "'"'"'<>]*\.'"$domain"'[^ "'"'"'<>]*' | sort -u || true)
    if [ -n "$matches" ]; then
        count=$(echo "$matches" | wc -l)
        echo "" >> "$OUTPUT_FILE"
        echo "[$domain] ($count referencias)" >> "$OUTPUT_FILE"
        echo "$matches" >> "$OUTPUT_FILE"
        echo "  → $domain: $count URLs únicas"
    fi
done

echo "" >> "$OUTPUT_FILE"
echo "--- Dominios de Terceros ---" >> "$OUTPUT_FILE"
for domain in "${THIRD_PARTY[@]}"; do
    matches=$(grep -rhi "$domain" "$STRINGS_DIR"/*.txt 2>/dev/null | grep -oE 'https?://[^ "'"'"'<>]+|[^ "'"'"'<>]*\.'"$domain"'[^ "'"'"'<>]*' | sort -u || true)
    if [ -n "$matches" ]; then
        count=$(echo "$matches" | wc -l)
        echo "" >> "$OUTPUT_FILE"
        echo "[$domain] ($count referencias)" >> "$OUTPUT_FILE"
        echo "$matches" >> "$OUTPUT_FILE"
        echo "  → $domain: $count URLs únicas"
    fi
done

# Paths de API
echo "" >> "$OUTPUT_FILE"
echo "--- Paths de API ---" >> "$OUTPUT_FILE"
grep -rhoE '/(api|aweme|v[0-9]+|service|monitor|log|report|track|analytics)[^ "'"'"'<> ]*' "$STRINGS_DIR"/*.txt 2>/dev/null | sort -u >> "$OUTPUT_FILE" || true

echo "" >> "$OUTPUT_FILE"
echo "--- URLs con 'log' / 'track' / 'report' / 'analytics' ---" >> "$OUTPUT_FILE"
grep -rhiE 'https?://[^ "'"'"'<>]*(log|track|report|analytics)[^ "'"'"'<>]*' "$STRINGS_DIR"/*.txt 2>/dev/null | sort -u >> "$OUTPUT_FILE" || true

total=$(wc -l < "$OUTPUT_FILE")
echo ""
echo "[✓] Análisis completado. $total líneas escritas en: $OUTPUT_FILE"
