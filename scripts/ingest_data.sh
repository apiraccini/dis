#!/usr/bin/env bash
# Ingest all example documents into a running DIS stack.
# Reads data/mapping.yaml, POSTs each file to the upload API.
# Usage: ./scripts/ingest_data.sh [base_url]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MAPPING="$ROOT_DIR/data/mapping.yaml"
FINAL_DIR="$ROOT_DIR/data/final"

BASE_URL="${1:-http://localhost:8000}"
UPLOAD_URL="$BASE_URL/api/documents/upload"

echo "=== DIS Example Data Ingestion ==="
echo "Upload URL: $UPLOAD_URL"
echo ""

FAILED=0

# Parse mapping.yaml. This is a deliberately minimal awk parser, NOT a general
# YAML reader: it assumes the exact format below — top-level keys ending in ':',
# two-space-indented '- ' list items, no quoting, no comments, no nesting.
#   filename:
#     - tag1
#     - tag2
parse_mapping() {
    awk '
    /^[^ ]/ && /:$/ {
        if (f) print f, tags
        f = $1; sub(/:$/, "", f); tags = ""; next
    }
    /^  - / {
        tag = $0; sub(/^[[:space:]]*- /, "", tag)
        if (tags) tags = tags "," tag; else tags = tag
    }
    END { if (f) print f, tags }
    ' "$MAPPING"
}

while IFS=' ' read -r filename tags; do
    filepath="$FINAL_DIR/$filename"

    if [ ! -f "$filepath" ]; then
        echo "  SKIP  $filename — file not found"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo -n "  POST  $filename (tags: $tags) ... "

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -F "file=@$filepath" \
        -F "tags=$tags" \
        "$UPLOAD_URL")

    case "$HTTP_CODE" in
        200) echo "ok (existing, dedup)" ;;
        202) echo "ok (ingested)" ;;
        *)   echo "FAILED (HTTP $HTTP_CODE)" && FAILED=$((FAILED + 1)) ;;
    esac
done < <(parse_mapping)

echo ""
if [ "$FAILED" -gt 0 ]; then
    echo "=== Ingestion finished with $FAILED failure(s) ==="
    exit 1
else
    echo "=== All documents ingested successfully ==="
fi
