#!/usr/bin/env bash
set -euo pipefail

OUT=/tmp/xray_run.txt
URL="http://127.0.0.1:8080"

# rimuovi vecchio file
rm -f "$OUT"

# lancia xray (modifica opzioni se vuoi)
xray webscan --url "$URL" --json-output "$OUT"

# breve controllo
if [ ! -s "$OUT" ]; then
  echo "Errore: $OUT mancante o vuoto"
  exit 2
fi

# esegui lo script Python che stampa i link e il primo body
python - <<'PY'
from utils import extract_xray_links, cat_html
links = extract_xray_links("/tmp/xray_run.txt")
print("LINKS TROVATI:", len(links))
for i,l in enumerate(links[:20],1):
    print(i, l)
if links:
    print("\n>> BODY PRIMO LINK:\n")
    print(cat_html(links[0]))
PY
