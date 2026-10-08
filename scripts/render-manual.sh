#!/usr/bin/env bash
# Render manual chapters to PDF and to GitHub Markdown (both formats are set in manual/_quarto.yml).
#   scripts/render-manual.sh                                    every chapter
#   scripts/render-manual.sh manual/chapters/05-settlement.qmd  one chapter
# Chapters that settle on chain start their own regtest node, so Bitcoin Core must be on PATH.
# The Markdown and its figures are committed; the PDFs are not.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ "$#" -eq 0 ]; then set -- manual/chapters/[0-9][0-9]-*.qmd; fi
for chapter in "$@"; do
  echo "== $chapter"
  uv run quarto render "$chapter"
done
