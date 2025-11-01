#!/usr/bin/env bash
# nightly_scrape.sh — refresh the ESPN+ schedule database
# Safety flags
set -euo pipefail

# -------- Config (override via env or edit here) --------
GEN_CMD="${GEN_CMD:-python3 espn_scraper.py}"
# Optional: set LOG_FILE to enable self-logging, e.g. LOG_FILE="$(pwd)/logs/nightly.log"
# -------------------------------------------------------

log() { printf '[%(%F %T)T] %s\n' -1 "$*"; }

# Avoid proxy inheritance
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# Optional self-logging
if [[ -n "${LOG_FILE:-}" ]]; then
  mkdir -p "$(dirname "$LOG_FILE")"
  exec >>"$LOG_FILE" 2>&1
fi

log "→ Running nightly DB refresh: $GEN_CMD"
bash -lc "$GEN_CMD"
log "✅ Nightly DB refresh completed."
