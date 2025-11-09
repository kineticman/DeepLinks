## v2.1.5 — 2025-11-08

- **M3U/XMLTV ID parity:** `tvg-id` now equals `dl-<playID>` to match XMLTV <channel id>.
- **Per-event M3U:** one `#EXTINF` per event (Option 1).
- **No functional change tonight:** DB showed all events ended by the time of generation; generator behavior unchanged.

## v2.1.0 — 2025-11-08

- **Fix:** M3U now writes one row per event reliably (works with dicts or objects).
- **Fix:** No undefined names; stable numeric tvg-ids; tvg-chno starts at 31000.
- **Improvement:** Live detection uses start/stop or explicit is_live; labels are consistent.
- **Note:** Replaces buggy v2.0.0 tag.

## v2.0.0 — 2025-11-08

- M3U now emits **one channel per event** (Option 1).
- Channel count uses a single run-time reference (consistent LIVE/Counts).
- Removed undefined names from prior injected block.
- Indentation normalized (tabs → 4 spaces).

# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0] - 2025-11-01
- Establish **DeepLinks** baseline (code + docs + sample outputs)
- Locks in the `sportscenter://...playID=<UUID>` deep-link scheme
- Includes `espn_scraper.py`, `generate_guide.py`, `SUMMARY.md`, `QUICKSTART_GUIDE.md`, `GUIDE_GENERATOR_README.md`
- Adds initial repo scaffolding files (.gitignore, LICENSE, README, CHANGELOG)

## v1.7.2 — 2025-11-01
- Generator: first `<display-name>` is event title; second is “ESPN+”.
- Fix: time-window query uses `julianday()` on both sides (no undercount).
- Minor: XMLTV/M3U counts now align with DB window; no behavior changes otherwise.

## v1.7.4 — 2025-11-01
- Generator: ultra-short M3U names (≤8 chars) for left-rail tiles.
- XMLTV: channel display-name shows event title; ESPN+ as alias.
- Window fix: use julianday() on both sides (no undercount).
- Shebang/exec fix for direct ./generate_guide.py usage.
