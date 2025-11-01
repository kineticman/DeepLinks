# DeepLinks

Turn ESPN+ schedule data into **deep-linkable virtual channels** and program guides (XMLTV + M3U) that launch streams via the custom URL scheme:

```
sportscenter://x-callback-url/showWatchStream?playID=<UUID>
```

This repository locks in the **baseline** consisting of:
- `espn_scraper.py` — pulls ESPN+ schedule and writes to `out/espn_schedule.db`
- `generate_guide.py` — reads from the DB to produce `espn_plus.xml` (XMLTV) and `espn_plus.m3u` (M3U)
- `SUMMARY.md`, `QUICKSTART_GUIDE.md`, `GUIDE_GENERATOR_README.md` — docs

> Baseline audit: see `DEEPLINKS_BASELINE_AUDIT.md` for a snapshot of counts and conventions.

---

## Quick Start (Python)

1) Create a virtual environment and install deps (if any)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # (if a requirements file is added later)
```

2) Scrape or refresh the schedule into SQLite
```bash
python espn_scraper.py
```

3) Generate XMLTV + M3U
```bash
python generate_guide.py
```

4) Point your consumer (e.g., Channels DVR) at the **XMLTV** and **M3U** you generated.  STRMLINK is the stream format on Custom Channels.

---

## Conventions

- All deep links use `sportscenter://x-callback-url/showWatchStream?playID=<UUID>`
- Time handling is **UTC** in DB; display/localization is left to consumers
- Standby/post blocks are currently fixed; will be parameterized in a future release

---

## Roadmap (short list)
- Parameterize standby/post durations and planning window
- Add validation checks (no negative durations, explicit gaps, channel-id stability)
- Optional `tvg-logo`/`tvg-chno` fields
- Minimal Docker wrapper for scrape + build
- CI lint + basic schema regression checks

---

## License
MIT — see `LICENSE`

---

## Acknowledgements
Built by Kineticman and collaborators.
