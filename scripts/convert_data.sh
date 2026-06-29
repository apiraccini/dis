#!/usr/bin/env bash
# Convert source markdown in data/raw/ to PDF and DOCX in data/final/.
# Only the PDF and DOCX variants are generated here; the .md, .txt, and .html
# files in data/final/ are authored/maintained directly, not produced by this script.
# Requires: pandoc + weasyprint (pip install weasyprint)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
RAW_DIR="$ROOT_DIR/data/raw"
FINAL_DIR="$ROOT_DIR/data/final"

# Detect pdf engine: weasyprint recommended for best Unicode support
PDF_ENGINE="weasyprint"
if ! command -v "$PDF_ENGINE" &>/dev/null; then
    PDF_ENGINE="pdflatex"
    echo "Warning: weasyprint not found, falling back to $PDF_ENGINE (may struggle with Unicode)"
fi

echo "=== Generating PDFs ==="
for src in engineering-handbook expense-policy data-privacy; do
    echo "  $src.md → $src.pdf"
    pandoc "$RAW_DIR/$src.md" -o "$FINAL_DIR/$src.pdf" --pdf-engine="$PDF_ENGINE"
done

echo "=== Generating DOCX ==="
for src in design-principles; do
    echo "  $src.md → $src.docx"
    pandoc "$RAW_DIR/$src.md" -o "$FINAL_DIR/$src.docx"
done

echo "=== Done ==="
ls -lh "$FINAL_DIR"/
