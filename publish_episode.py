#!/usr/bin/env python3
"""Publish an Adam and Eve FM episode to the private GitHub Pages podcast feed.

Usage:
  python3 /home/box/podcast/publish_episode.py --mp3 /path/to/episode.mp3 --date 2026-10-05 \
      [--chapters /path/to/chapters.json] [--title "..."] [--description "..."] \
      [--pubdate "2026-10-05 12:00"] [--replace] [--no-push]

One-off / special episodes (backward-compatible; weekly usage above is unchanged):
  python3 /home/box/podcast/publish_episode.py --mp3 /path/special.mp3 --date 2026-09-28 \
      --slug 2026-09-28-hims-no-es-telemedicina --title "HIMS Isn't Telemedicine — Adan vs Eve (Special)" \
      --description-file /path/show-notes.txt [--chapters chapters.json --append-chapters]

- Episodes are keyed by slug. Without --slug the slug is "<date>-weekly-thesis-review" (the historical
  date-keyed behavior: same file name, same guid, one weekly episode per date).
- With --slug the MP3 goes to episodes/<slug>.mp3 and the guid is "<slug>", so a special on the same date
  never collides with (or replaces) that date's weekly episode.

- Copies the MP3 to episodes/<slug>.mp3 in the repo clone (default slug: <date>-weekly-thesis-review)
- Adds/updates the episode in episodes.json (source of truth) and regenerates feed.xml
- Commits and pushes to main (GitHub Pages rebuilds automatically)
Config: /home/box/podcast/config.json  {"repo": "owner/name", "base_url": "https://owner.github.io/name", "clone": "/home/box/podcast/repo"}
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

TZ = ZoneInfo("America/New_York")
CONFIG = Path(os.environ.get("WTR_CONFIG", "/home/box/podcast/config.json"))

DEFAULT_SHOW = {
    "title": "Adam and Eve FM",
    "author": "Adam and Eve FM",
    "summary": "Adam (bull) and Eve (skeptic) debate markets, theses, articles and big ideas, casual and fun.",
    "language": "en-us",
}

def run(cmd, cwd=None):
    print("+", " ".join(cmd)); subprocess.run(cmd, cwd=cwd, check=True)

def duration(p):
    s = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode().strip())
    s = int(round(s)); return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

WEEKLY_SUFFIX = "weekly-thesis-review"

def slug_of(ep):
    """Episode key. Legacy (date-keyed) entries have no 'slug' field: derive it from the date."""
    return ep.get("slug") or f"{ep['date']}-{WEEKLY_SUFFIX}"

def valid_slug(s):
    import re
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,120}", s):
        raise argparse.ArgumentTypeError("slug must be lowercase letters, digits and hyphens")
    return s

def build_feed(cfg, episodes):
    base = cfg["base_url"].rstrip("/")
    show = {**DEFAULT_SHOW, **cfg.get("show", {})}
    cover = cfg.get("cover", "cover-v3.jpg")
    items = []
    for ep in sorted(episodes, key=lambda e: e["pub_iso"], reverse=True):
        pub = format_datetime(datetime.fromisoformat(ep["pub_iso"]))
        url = f"{base}/episodes/{ep['file']}"
        items.append(f"""    <item>
      <title>{escape(ep['title'])}</title>
      <description>{escape(ep['description'])}</description>
      <itunes:summary>{escape(ep['description'])}</itunes:summary>
      <itunes:author>{escape(show['author'])}</itunes:author>
      <enclosure url="{escape(url)}" length="{ep['length']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(ep['guid'])}</guid>
      <pubDate>{pub}</pubDate>
      <itunes:duration>{ep['duration']}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>{escape(ep.get('episode_type', 'full'))}</itunes:episodeType>
    </item>""")
    last = format_datetime(datetime.now(TZ))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(show['title'])}</title>
    <link>{escape(base)}/</link>
    <atom:link href="{escape(base)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{escape(show['summary'])}</description>
    <language>{show['language']}</language>
    <lastBuildDate>{last}</lastBuildDate>
    <itunes:author>{escape(show['author'])}</itunes:author>
    <itunes:summary>{escape(show['summary'])}</itunes:summary>
    <itunes:owner><itunes:name>{escape(show['author'])}</itunes:name></itunes:owner>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:image href="{escape(base)}/{escape(cover)}"/>
    <image><url>{escape(base)}/{escape(cover)}</url><title>{escape(show['title'])}</title><link>{escape(base)}/</link></image>
    <itunes:category text="Business">
      <itunes:category text="Investing"/>
    </itunes:category>
    <itunes:block>Yes</itunes:block>
{chr(10).join(items)}
  </channel>
</rss>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp3", required=True)
    ap.add_argument("--date", required=True, help="Episode date YYYY-MM-DD")
    ap.add_argument("--chapters", help="chapters.json from render.py (titles go into description)")
    ap.add_argument("--title"); ap.add_argument("--description")
    ap.add_argument("--description-file", help="read the show notes/description from a UTF-8 text file")
    ap.add_argument("--slug", type=valid_slug, help="one-off episode key/file name, e.g. 2026-09-28-hims-no-es-telemedicina (default: <date>-weekly-thesis-review)")
    ap.add_argument("--append-chapters", action="store_true", help="append chapter titles to a custom --description/--description-file")
    ap.add_argument("--episode-type", choices=["full", "bonus", "trailer"], default="full")
    ap.add_argument("--pubdate", help="'YYYY-MM-DD HH:MM' America/New_York (default: now)")
    ap.add_argument("--replace", action="store_true", help="replace an existing episode with the same slug (i.e. same date for weekly episodes)")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    repo = Path(cfg["clone"])
    d = datetime.strptime(a.date, "%Y-%m-%d")
    title = a.title or f"Adam and Eve FM — {d.strftime('%b')} {d.day}, {d.year}"
    if a.description and a.description_file:
        sys.exit("use either --description or --description-file, not both")
    custom = a.description or (Path(a.description_file).read_text(encoding="utf-8").strip() if a.description_file else None)
    chap = ""
    if a.chapters:
        ch = json.loads(Path(a.chapters).read_text())
        chap = "Chapters: " + "; ".join(f"{c['id']}. {c['title']}" for c in ch) + "."
    if custom:
        desc = custom + ("\n\n" + chap if (chap and a.append_chapters) else "")
    else:
        desc = "Adan (bull) vs Eve (skeptic) debate the week's portfolio thesis."
        if chap:
            desc += " " + chap
    pub = datetime.strptime(a.pubdate, "%Y-%m-%d %H:%M").replace(tzinfo=TZ) if a.pubdate else datetime.now(TZ).replace(microsecond=0)

    slug = a.slug or f"{a.date}-{WEEKLY_SUFFIX}"
    fname = f"{slug}.mp3"
    (repo / "episodes").mkdir(exist_ok=True)
    dest = repo / "episodes" / fname

    epj = repo / "episodes.json"
    episodes = json.loads(epj.read_text()) if epj.exists() else []
    existing = [e for e in episodes if slug_of(e) == slug]
    if existing and not a.replace:
        sys.exit(f"Episode '{slug}' already exists; use --replace")
    if any(e["file"] == fname for e in episodes if slug_of(e) != slug):
        sys.exit(f"File name {fname} is already used by another episode")
    shutil.copyfile(a.mp3, dest)
    before = len(episodes)
    episodes = [e for e in episodes if slug_of(e) != slug]
    if a.slug:
        guid = existing[0]["guid"] if existing else slug
    else:
        guid = existing[0]["guid"] if existing else f"{WEEKLY_SUFFIX}-{a.date}"
    entry = {"date": a.date, "title": title, "description": desc, "file": fname,
             "length": dest.stat().st_size, "duration": duration(dest),
             "pub_iso": pub.isoformat(), "guid": guid}
    if a.slug:
        entry["slug"] = slug
    if a.episode_type != "full":
        entry["episode_type"] = a.episode_type
    episodes.append(entry)
    assert len(episodes) == before + (0 if existing else 1)
    epj.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n")

    feed = build_feed(cfg, episodes)
    ET.fromstring(feed.encode())  # validate
    (repo / "feed.xml").write_text(feed)
    for f in (".nojekyll",):
        (repo / f).touch()
    if not (repo / "index.html").exists():
        (repo / "index.html").write_text("<!doctype html><meta charset=utf-8><meta name=robots content=noindex><title>.</title>\n")
    here = Path(__file__).resolve()
    if here.parent != repo.resolve():
        shutil.copyfile(here, repo / "publish_episode.py")

    run(["git", "add", "-A"], cwd=repo)
    run(["git", "commit", "-m", f"Publish episode {slug}"], cwd=repo)
    if not a.no_push:
        run(["git", "push", "origin", "main"], cwd=repo)
    print("Feed:", cfg["base_url"].rstrip("/") + "/feed.xml")
    print("Episode:", cfg["base_url"].rstrip("/") + "/episodes/" + fname)

if __name__ == "__main__":
    main()
