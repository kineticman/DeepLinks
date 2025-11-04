#!/usr/bin/env bash
# hourly.sh — regenerate guide, then tell Channels DVR to reload M3U and XMLTV
set -euo pipefail

# Resolve this script's directory even when run from cron/symlink
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

# -------- Config (override via env or edit here) --------
HOST="${HOST:-http://127.0.0.1:8089}"
M3U_SOURCE="${M3U_SOURCE:-streamlinks}"
XMLTV_ID="${XMLTV_ID:-XMLTV-streamlinks}"
DELAY="${DELAY:-20}"

# Default generator command; can be overridden via env GEN_CMD/GEN_ARGS
GEN_CMD="${GEN_CMD:-python3}"
GEN_ARGS="${GEN_ARGS:-"${SCRIPT_DIR}/generate_guide.py"}"
# -------------------------------------------------------

log() { printf '[%(%F %T)T] %s\n' -1 "$*"; }

# Avoid proxy inheritance (per your standing rule)
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 1) Build guide
log "→ Running: ${GEN_CMD} ${GEN_ARGS}"
"${GEN_CMD}" ${GEN_ARGS}

# 2) Wait
log "→ Sleeping ${DELAY}s"
sleep "${DELAY}"

# 3) Reload M3U provider
log "→ POST ${HOST}/providers/m3u/sources/${M3U_SOURCE}/refresh"
curl -sS --fail -m 20 -X POST "${HOST}/providers/m3u/sources/${M3U_SOURCE}/refresh" | sed 's/^/  body: /'
log "✓ M3U refresh requested"

# 4) Wait
log "→ Sleeping ${DELAY}s"
sleep "${DELAY}"

# 5) Redownload XMLTV lineup
log "→ PUT ${HOST}/dvr/lineups/${XMLTV_ID}"
curl -sS --fail -m 30 -X PUT "${HOST}/dvr/lineups/${XMLTV_ID}" | sed 's/^/  body: /'
log "✓ XMLTV refresh requested"

log "✅ All steps completed."
