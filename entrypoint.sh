#!/usr/bin/env bash
set -euo pipefail

CRONTAB_FILE="/etc/crontabs/root"

log() { printf '%s %s\n' "[$(date -Iseconds)]" "$*"; }

CRON_HOURLY="${CRON_HOURLY:-5 * * * *}"
CRON_NIGHTLY="${CRON_NIGHTLY:-15 3 * * *}"

mkdir -p /etc/crontabs

log "Initial scrape → guide..."
python3 /app/espn_scraper.py
python3 /app/generate_guide.py

log "Starting http server for espn_guide.xml..."
python3 -u /app/serve_out.py --host 0.0.0.0 >> /proc/1/fd/1 2>> /proc/1/fd/2 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' TERM INT

log "Installing cron schedules..."

cat >"$CRONTAB_FILE" <<EOF
SHELL=/bin/sh

${CRON_HOURLY}  /bin/sh -lc 'cd /app && ./hourly.sh' >> /proc/1/fd/1 2>&1
${CRON_NIGHTLY} /bin/sh -lc 'cd /app && ./nightly_scrape.sh' >> /proc/1/fd/1 2>&1
EOF

chmod 600 "$CRONTAB_FILE"

log "Run initial hourly reload..."
./hourly.sh

log "Starting crond (background) and waiting on processes..."
crond -b -l 8 -c /etc/crontabs -L /proc/1/fd/1

wait "$SERVER_PID"
