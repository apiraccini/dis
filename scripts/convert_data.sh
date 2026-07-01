#!/usr/bin/env bash
# Convert source markdown in data/raw/ to PDF and DOCX in data/final/.
# Only the PDF and DOCX variants are generated here; the .md, .txt, and .html
# files in data/final/ are authored/maintained directly, not produced by this script.
# Requires: pandoc + weasyprint (pip install weasyprint); architecture-overview's
# rasterized (image-only) PDF additionally requires PyMuPDF (uv sync in backend/).
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
    # cd into RAW_DIR so weasyprint resolves relative image paths (e.g.
    # engineering-handbook's embedded ci-pipeline-diagram.png) against it.
    (cd "$RAW_DIR" && pandoc "$src.md" -o "$FINAL_DIR/$src.pdf" --pdf-engine="$PDF_ENGINE")
done

echo "=== Generating rasterized (image-only) PDF ==="
# architecture-overview showcases VLM-assisted extraction: render to a normal
# PDF first, then rasterize each page to an image and rebuild a PDF with no
# text layer at all, simulating a scanned document.
echo "  architecture-overview.md → architecture-overview.pdf (scanned, no text layer)"
TMP_TEXT_PDF="$(mktemp --suffix=.pdf)"
pandoc "$RAW_DIR/architecture-overview.md" -o "$TMP_TEXT_PDF" --pdf-engine="$PDF_ENGINE"
uv run --project "$ROOT_DIR/backend" python - "$TMP_TEXT_PDF" "$FINAL_DIR/architecture-overview.pdf" <<'PYEOF'
import sys
import fitz

src_path, dst_path = sys.argv[1], sys.argv[2]
src = fitz.open(src_path)
dst = fitz.open()
for page in src:
    pix = page.get_pixmap(dpi=150)
    new_page = dst.new_page(width=pix.width, height=pix.height)
    new_page.insert_image(new_page.rect, pixmap=pix)
dst.save(dst_path)
dst.close()
src.close()
PYEOF
rm -f "$TMP_TEXT_PDF"

echo "=== Generating DOCX ==="
for src in design-principles; do
    echo "  $src.md → $src.docx"
    pandoc "$RAW_DIR/$src.md" -o "$FINAL_DIR/$src.docx"
done

echo "=== Done ==="
ls -lh "$FINAL_DIR"/
