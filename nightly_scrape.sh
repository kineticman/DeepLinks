#!/usr/bin/env bash
# nightly_scrape.sh — refresh the ESPN+ schedule database
set -euo pipefail

# Resolve this script's directory even when run from cron/symlink
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# -------- Config (override via env or edit here) --------
# You can point GEN_CMD at a venv python if you want.
GEN_CMD="${GEN_CMD:-python3}"
GEN_ARGS="${GEN_ARGS:-${SCRIPT_DIR}/espn_scraper.py}"
# Optional: set LOG_FILE for self-logging (cron already redirects for you)
# LOG_FILE="${LOG_FILE:-}"
# -------------------------------------------------------

log() { printf '[%(%F %T)T] %s\n' -1 "$*"; }

# Avoid proxy inheritance (your standing rule)
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# Optional self-logging
if [[ -n "${LOG_FILE:-}" ]]; then
  mkdir -p "$(dirname "$LOG_FILE")"
  exec >>"$LOG_FILE" 2>&1
fi

log "→ Running nightly DB refresh: ${GEN_CMD} ${GEN_ARGS}"
"${GEN_CMD}" ${GEN_ARGS}
log "✅ Nightly DB refresh completed."
