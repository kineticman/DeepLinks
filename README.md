# DeepLinks

Turn ESPN+ schedule data into **deep-linkable virtual channels** and program guides (XMLTV + M3U) that launch streams via a custom URL scheme:

```
sportscenter://x-callback-url/showWatchStream?playID=<UUID>
```

This repository includes:
- `espn_scraper.py` — pulls ESPN+ schedule into `out/espn_schedule.db`
- `generate_guide.py` — reads from the DB to produce `out/espn_plus.xml` (XMLTV) and `out/espn_plus.m3u` (M3U)
- `hourly.sh` — helper to regenerate the guide and notify Channels DVR to reload sources
- `nightly_scrape.sh` — helper to refresh the ESPN+ schedule database once nightly
- Docs: `SUMMARY.md`, `QUICKSTART_GUIDE.md`, `GUIDE_GENERATOR_README.md`

> For a baseline snapshot of counts and conventions, see `DEEPLINKS_BASELINE_AUDIT.md` (if provided).

---

## Quick Start

1) Scrape or refresh the schedule into SQLite:
```bash
python3 espn_scraper.py
```

2) Generate XMLTV + M3U:
```bash
python3 generate_guide.py
```

3) Point your consumer (e.g., Channels DVR) at the generated **XMLTV** and **M3U** files under `out/`.  
   _Note:_ STRMLINK is the expected stream format for Custom Channels.

Defaults: the scraper loads ~4 days; the M3U generator emits channels for events **LIVE NOW** and within the next ~3 hours.

---

## Automated Hourly Refresh (recommended)

Use `hourly.sh` to regenerate the guide and then tell Channels DVR to reload your **M3U** and **XMLTV** sources (with a 20‑second pause between steps by default).

**What it does:**
1. Runs `generate_guide.py`
2. `POST /providers/m3u/sources/<name>/refresh` (e.g., `streamlinks`)
3. `PUT /dvr/lineups/<XMLTV-ID>` (e.g., `XMLTV-streamlinks`)

**Defaults inside `hourly.sh`:**
- `HOST`: `http://127.0.0.1:8089` (override to your Channels DVR host:port)
- `M3U_SOURCE`: `streamlinks`
- `XMLTV_ID`: `XMLTV-streamlinks`
- `DELAY`: `20` (seconds between steps)
- `GEN_CMD`: `python3 generate_guide.py`

### Run it manually
```bash
./hourly.sh
```

You can also override settings without editing the file:
```bash
HOST=http://192.168.1.50:8089 DELAY=30 ./hourly.sh
```

### Install as a cron job (hourly)

Replace `<APP_DIR>` with your clone’s absolute path.

```bash
mkdir -p <APP_DIR>/logs

( crontab -l 2>/dev/null | grep -v '<APP_DIR>/hourly.sh' ;   echo 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' ;   echo '0 * * * * /usr/bin/flock -n /tmp/deeplinks_hourly.lock /bin/bash <APP_DIR>/hourly.sh >> <APP_DIR>/logs/hourly.log 2>&1' ) | crontab -

crontab -l
```

The `flock` guard prevents overlapping runs if one hour’s job hasn’t finished before the next starts.

---

## Nightly DB Refresh (recommended)

Use `nightly_scrape.sh` to refresh the ESPN+ schedule database once per night. This keeps the next few days’ listings fresh without hammering upstream.

**What it does:**
- Runs `python3 espn_scraper.py`

**Defaults inside `nightly_scrape.sh`:**
- `GEN_CMD`: `python3 espn_scraper.py`

### Run it manually
```bash
./nightly_scrape.sh
```

You can optionally enable self‑logging per invocation:
```bash
LOG_FILE="$(pwd)/logs/nightly.log" ./nightly_scrape.sh
```

### Install as a cron job (3:30 AM nightly)
```bash
APP_DIR="<ABSOLUTE_PATH_TO_CLONE>"
mkdir -p "$APP_DIR/logs"

( crontab -l 2>/dev/null | grep -v "$APP_DIR/nightly_scrape.sh" ;   echo 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' ;   echo '30 3 * * * /usr/bin/flock -n /tmp/deeplinks_nightly.lock /bin/bash '"$APP_DIR"'/nightly_scrape.sh >> '"$APP_DIR"'/logs/nightly.log 2>&1' ) | crontab -

crontab -l
```

---

## Conventions

- Deep links use `sportscenter://x-callback-url/showWatchStream?playID=<UUID>`
- Times are stored as **UTC** in the DB; display/localization is left to consumers
- “Standby / post” filler behavior is fixed for now and may be parameterized later

---

## Roadmap (short list)

- Parameterize standby/post durations and planning window
- Add validation checks (no negative durations, explicit gaps, channel‑id stability)
- Optional `tvg-logo` / `tvg-chno` fields
- Minimal Docker wrapper for scrape + build
- CI lint + basic schema regression checks

---

## License

MIT — see `LICENSE`.

---

## Acknowledgements

Built by Kineticman and collaborators.
