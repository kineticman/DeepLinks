
#!/usr/bin/env python3
# DeepLinks — ESPN+ M3U/XMLTV generator
# - Stable channel ids: dl-<event id>
# - M3U skips ended events (XMLTV keeps 30m "EVENT ENDED" stubs for already-ended events)
# - Include LIVE and next ~3 hours; keep events until 65 min after end
# - Standby blocks: 30m tiles up to 6h ahead of start (skip <5m slivers)
# - Channel display-name: <short event title>, then "ESPN+"
# - FIX: Use julianday() on BOTH sides of time window comparisons (no string-compare undercount)

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List
import xml.etree.ElementTree as ET

# --- Tunables ---------------------------------------------------------------

DB_PATH = os.environ.get("DEEPLINKS_DB", "out/espn_schedule.db")
OUT_XML = os.environ.get("DEEPLINKS_XML", "out/espn_plus.xml")
OUT_M3U = os.environ.get("DEEPLINKS_M3U", "out/espn_plus.m3u")

PLANNING_WINDOW_HOURS = int(os.environ.get("DEEPLINKS_WINDOW_HOURS", "3"))
MAX_STANDBY_HOURS = int(os.environ.get("DEEPLINKS_MAX_STANDBY_HOURS", "6"))
STANDBY_TILE_MIN = int(os.environ.get("DEEPLINKS_STANDBY_TILE_MIN", "30"))

POST_END_GRACE_MIN = int(os.environ.get("DEEPLINKS_POST_END_GRACE_MIN", "65"))
EVENT_ENDED_DURATION_MIN = int(os.environ.get("DEEPLINKS_ENDED_TILE_MIN", "30"))

GROUP_TITLE = os.environ.get("DEEPLINKS_GROUP", "ESPN+")
PROVIDER_LABEL = os.environ.get("DEEPLINKS_PROVIDER_LABEL", "ESPN+")

# --- Helpers ----------------------------------------------------------------

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def parse_iso_z(s: str) -> datetime:
    # Accepts "YYYY-MM-DDTHH:MM:SSZ"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)

def to_xmltv_dt(dt_: datetime) -> str:
    # XMLTV wants: YYYYMMDDHHMMSS +0000 (with a space before offset)
    return dt_.strftime("%Y%m%d%H%M%S +0000")

def minutes_between(a: datetime, b: datetime) -> int:
    return int(round((b - a).total_seconds() / 60.0))

_title_emoji_re = re.compile(r'[\u2000-\u206F\u2100-\u27FF\uFE00-\uFE0F]+')

def shorten_title(s: str, max_len: int = 38) -> str:
    if not s:
        return "Unknown Event"
    s = _title_emoji_re.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= max_len:
        return s
    cut = s[: max_len + 1]
    cut = cut.rsplit(" ", 1)[0]
    return (cut or s[:max_len]).rstrip() + "…"

def _jd_fmt(dt_: datetime) -> str:
    # SQLite-friendly UTC datetime: "YYYY-MM-DD HH:MM:SS+00:00"
    return dt_.strftime("%Y-%m-%d %H:%M:%S+00:00")

# --- Data model -------------------------------------------------------------

@dataclass
class Event:
    id: str
    title: str
    sport: str | None
    league: str | None
    start: datetime
    stop: datetime
    status: str | None = None

# --- DB ---------------------------------------------------------------------

def load_events_for_window(
    db_path: str,
    window_hours: int = PLANNING_WINDOW_HOURS,
    post_end_grace_min: int = POST_END_GRACE_MIN,
) -> List[Event]:
    """
    Return events that are LIVE now or start within `window_hours`,
    and also keep recently-ended events for `post_end_grace_min`.
    (Uses julianday() on both sides to avoid string-compare issues.)
    """
    now = now_utc()
    window_end = now + timedelta(hours=window_hours)
    grace_cutoff = now - timedelta(minutes=post_end_grace_min)

    q = """
    SELECT id, title, sport, league, start_utc, stop_utc, status
    FROM events
    WHERE
      julianday(replace(start_utc,'Z','+00:00')) <= julianday(?)
      AND julianday(replace(stop_utc,'Z','+00:00')) >= julianday(?)
    ORDER BY start_utc, title, id
    """
    params = (_jd_fmt(window_end), _jd_fmt(grace_cutoff))

    rows: List[Event] = []
    with sqlite3.connect(db_path) as cx:
        for r in cx.execute(q, params):
            start = parse_iso_z(r[4])
            stop = parse_iso_z(r[5])
            rows.append(
                Event(
                    id=r[0],
                    title=r[1] or "",
                    sport=r[2],
                    league=r[3],
                    start=start,
                    stop=stop,
                    status=r[6],
                )
            )
    # Deduplicate by id (belt & suspenders)
    return list({e.id: e for e in rows}.values())

# --- XMLTV generation -------------------------------------------------------

def emit_channel(tv: ET.Element, ev: Event) -> str:
    """
    Create <channel id="dl-<event id>">.
    First <display-name> is the event title (shortened).
    Second <display-name> is 'ESPN+' (provider label).
    """
    chan_id = f"dl-{ev.id}"
    ch = ET.SubElement(tv, "channel", id=chan_id)
    ET.SubElement(ch, "display-name").text = shorten_title(ev.title)
    ET.SubElement(ch, "display-name").text = PROVIDER_LABEL
    return chan_id

def emit_programme(
    tv: ET.Element,
    chan_id: str,
    start: datetime,
    stop: datetime,
    title: str,
    categories: Iterable[str] = (),
) -> None:
    p = ET.SubElement(
        tv,
        "programme",
        {"start": to_xmltv_dt(start), "stop": to_xmltv_dt(stop), "channel": chan_id},
    )
    t = ET.SubElement(p, "title")
    t.set("lang", "en")
    t.text = title
    for c in categories:
        ce = ET.SubElement(p, "category")
        ce.set("lang", "en")
        ce.text = c

def generate_xmltv(events: List[Event], out_path: str) -> None:
    tv = ET.Element("tv")
    now = now_utc()

    # Emit channels (one per event)
    chan_ids: dict[str, str] = {}
    for ev in events:
        chan_ids[ev.id] = emit_channel(tv, ev)

    # Emit programmes per event channel
    for ev in events:
        chan = chan_ids[ev.id]

        # Standby tiles BEFORE start (only for upcoming)
        if ev.start > now:
            pre_max = min(ev.start - now, timedelta(hours=MAX_STANDBY_HOURS))
            if pre_max.total_seconds() > 0:
                cursor = ev.start - pre_max
                # align to STANDBY_TILE_MIN grid
                align_min = (cursor.minute // STANDBY_TILE_MIN) * STANDBY_TILE_MIN
                cursor = cursor.replace(minute=align_min, second=0, microsecond=0)
                while cursor < ev.start:
                    block_end = min(cursor + timedelta(minutes=STANDBY_TILE_MIN), ev.start)
                    # Skip micro-slivers <5m
                    if minutes_between(cursor, block_end) >= 5:
                        emit_programme(tv, chan, cursor, block_end, "STAND BY")
                    cursor += timedelta(minutes=STANDBY_TILE_MIN)

        # The event itself
        cats = ["Sports", "Sports event"]
        if ev.sport:
            cats.append(ev.sport)
        if ev.league:
            cats.append(ev.league)
        emit_programme(tv, chan, ev.start, ev.stop, ev.title, cats)

        # Post tile only if already ended (visible stub)
        if ev.stop <= now + timedelta(minutes=1):
            end_stub = ev.stop + timedelta(minutes=EVENT_ENDED_DURATION_MIN)
            emit_programme(tv, chan, ev.stop, end_stub, "EVENT ENDED")

    # Pretty-print (Python 3.9+)
    try:
        ET.indent(tv)  # type: ignore[attr-defined]
    except Exception:
        pass
    ET.ElementTree(tv).write(out_path, encoding="utf-8", xml_declaration=True)

# --- M3U generation ---------------------------------------------------------

def deep_link_for(ev: Event) -> str:
    # sportscenter://x-callback-url/showWatchStream?playID=<UUID>
    return f"sportscenter://x-callback-url/showWatchStream?playID={ev.id}"

def generate_m3u(events: List[Event], out_path: str) -> None:
    now = now_utc()
    lines = ["#EXTM3U"]
    idx = 1  # cosmetic numbering

    for ev in events:
        # Hide ended events from M3U but keep in XMLTV
        if ev.stop < now:
            continue

        tvg_id = f"dl-{ev.id}"
        short = shorten_title(ev.title)
        suffix = ev.league or ev.sport or ""
        ch_name = f"{GROUP_TITLE} {idx}: {short}" + (f" ({suffix})" if suffix else "")

        lines.append(
            f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{ch_name}" tvg-logo="" group-title="{GROUP_TITLE}",{ch_name}'
        )
        lines.append(deep_link_for(ev))
        idx += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

# --- CLI --------------------------------------------------------------------

def summarize_run(events: List[Event]) -> None:
    now_str = now_utc().strftime("%Y-%m-%d %H:%M:%S UTC")
    print("ESPN+ M3U/XMLTV Generator")
    print("============================================================")
    print(f"Database: {os.path.abspath(DB_PATH)}")
    print(f"Time: {now_str}\n")
    print(f"Fetching live and upcoming events (next {PLANNING_WINDOW_HOURS} hours)...")
    print(f"Found {len(events)} events\n")

    print("Generating M3U playlist...")
    generate_m3u(events, OUT_M3U)
    m3u_count = 0
    try:
        with open(OUT_M3U, "r", encoding="utf-8") as fh:
            m3u_count = sum(1 for ln in fh if ln.startswith("#EXTINF"))
    except FileNotFoundError:
        pass
    print(f"  Saved: {os.path.abspath(OUT_M3U)}")
    print(f"  Channels: {m3u_count}\n")

    print("Generating XMLTV guide...")
    generate_xmltv(events, OUT_XML)
    print(f"  Saved: {os.path.abspath(OUT_XML)}\n")

    # Sample titles
    print("Sample events:")
    print("------------------------------------------------------------")
    for i, ev in enumerate(events[:5], 1):
        live = "🔴 LIVE - " if ev.start <= now_utc() <= ev.stop else ""
        print(f"{i}. {live}{ev.title}")
    if len(events) > 5:
        print(f"... and {len(events)-5} more\n")

    print("============================================================")
    print("✓ Generation complete!\n")
    print("Files created:")
    print(f"  M3U:  {os.path.abspath(OUT_M3U)}")
    print(f"  XMLTV: {os.path.abspath(OUT_XML)}")

def main() -> None:
    # Ensure output dirs exist
    os.makedirs(os.path.dirname(OUT_XML), exist_ok=True)
    os.makedirs(os.path.dirname(OUT_M3U), exist_ok=True)

    events = load_events_for_window(
        DB_PATH,
        window_hours=PLANNING_WINDOW_HOURS,
        post_end_grace_min=POST_END_GRACE_MIN,
    )
    # Stable ordering already in SQL; keep a final sort for determinism
    events.sort(key=lambda e: (e.start, e.title, e.id))
    summarize_run(events)

if __name__ == "__main__":
    main()
