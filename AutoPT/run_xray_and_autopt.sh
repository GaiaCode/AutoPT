#!/usr/bin/env bash
set -euo pipefail

URL="${1:-http://127.0.0.1:8080}"
XRAY_OUT="/tmp/xray_scan.json"
LOG_OUT="/tmp/autopt_run.log"

rm -f "$XRAY_OUT" "$LOG_OUT"

echo "[*] Avvio xray su $URL"
xray webscan --url "$URL" --json-output "$XRAY_OUT"

if [ ! -s "$XRAY_OUT" ]; then
  echo "[!] Nessun output xray"
  exit 2
fi

echo "[*] Parsing link dal JSON"
python - <<'PY'
from utils import extract_xray_links, cat_html
links = extract_xray_links("/tmp/xray_scan.json")
print(f"Trovati {len(links)} link")
for i, l in enumerate(links[:10], 1):
    print(i, l)
if links:
    print("\n[HTML preview primo link]")
    print(cat_html(links[0]))
PY

echo "[*] Avvio AutoPT..."
python main.py "$URL" | tee "$LOG_OUT"
