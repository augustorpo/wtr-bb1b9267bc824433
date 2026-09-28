#!/usr/bin/env python3
"""Publish a Weekly Thesis Review episode to the private GitHub Pages podcast feed.

Usage:
  python3 /home/box/podcast/publish_episode.py --mp3 /path/to/episode.mp3 --date 2026-10-05 \
      [--chapters /path/to/chapters.json] [--title "..."] [--description "..."] \
      [--pubdate "2026-10-05 12:00"] [--replace] [--no-push]

- Copies the MP3 to episodes/<date>-weekly-thesis-review.mp3 in the repo clone
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

SHOW = {
    "title": "Weekly Thesis Review",
    "author": "Bull vs Skeptic FM",
    "summary": "Private weekly investment debate: Adan (bull) vs Eve (skeptic) stress-test the portfolio thesis.",
    "language": "en-us",
}

def run(cmd, cwd=None):
    print("+", " ".join(cmd)); subprocess.run(cmd, cwd=cwd, check=True)

def duration(p):
    s = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode().strip())
    s = int(round(s)); return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"

def build_feed(cfg, episodes):
    base = cfg["base_url"].rstrip("/")
    items = []
    for ep in sorted(episodes, key=lambda e: e["pub_iso"], reverse=True):
        pub = format_datetime(datetime.fromisoformat(ep["pub_iso"]))
        url = f"{base}/episodes/{ep['file']}"
        items.append(f"""    <item>
      <title>{escape(ep['title'])}</title>
      <description>{escape(ep['description'])}</description>
      <itunes:summary>{escape(ep['description'])}</itunes:summary>
      <itunes:author>{escape(SHOW['author'])}</itunes:author>
      <enclosure url="{escape(url)}" length="{ep['length']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(ep['guid'])}</guid>
      <pubDate>{pub}</pubDate>
      <itunes:duration>{ep['duration']}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
      <itunes:episodeType>full</itunes:episodeType>
    </item>""")
    last = format_datetime(datetime.now(TZ))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(SHOW['title'])}</title>
    <link>{escape(base)}/</link>
    <atom:link href="{escape(base)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{escape(SHOW['summary'])}</description>
    <language>{SHOW['language']}</language>
    <lastBuildDate>{last}</lastBuildDate>
    <itunes:author>{escape(SHOW['author'])}</itunes:author>
    <itunes:summary>{escape(SHOW['summary'])}</itunes:summary>
    <itunes:owner><itunes:name>{escape(SHOW['author'])}</itunes:name></itunes:owner>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:image href="{escape(base)}/cover.jpg"/>
    <image><url>{escape(base)}/cover.jpg</url><title>{escape(SHOW['title'])}</title><link>{escape(base)}/</link></image>
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
    ap.add_argument("--pubdate", help="'YYYY-MM-DD HH:MM' America/New_York (default: now)")
    ap.add_argument("--replace", action="store_true", help="replace an existing episode with the same date")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    cfg = json.loads(CONFIG.read_text())
    repo = Path(cfg["clone"])
    d = datetime.strptime(a.date, "%Y-%m-%d")
    title = a.title or f"Weekly Thesis Review — {d.strftime('%b')} {d.day}, {d.year}"
    if a.description:
        desc = a.description
    else:
        desc = "Adan (bull) vs Eve (skeptic) debate the week's portfolio thesis."
        if a.chapters:
            ch = json.loads(Path(a.chapters).read_text())
            desc += " Chapters: " + "; ".join(f"{c['id']}. {c['title']}" for c in ch) + "."
    pub = datetime.strptime(a.pubdate, "%Y-%m-%d %H:%M").replace(tzinfo=TZ) if a.pubdate else datetime.now(TZ).replace(microsecond=0)

    fname = f"{a.date}-weekly-thesis-review.mp3"
    (repo / "episodes").mkdir(exist_ok=True)
    dest = repo / "episodes" / fname
    shutil.copyfile(a.mp3, dest)

    epj = repo / "episodes.json"
    episodes = json.loads(epj.read_text()) if epj.exists() else []
    existing = [e for e in episodes if e["date"] == a.date]
    if existing and not a.replace:
        sys.exit(f"Episode for {a.date} already exists; use --replace")
    episodes = [e for e in episodes if e["date"] != a.date]
    guid = existing[0]["guid"] if existing else f"weekly-thesis-review-{a.date}"
    episodes.append({"date": a.date, "title": title, "description": desc, "file": fname,
                     "length": dest.stat().st_size, "duration": duration(dest),
                     "pub_iso": pub.isoformat(), "guid": guid})
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
    run(["git", "commit", "-m", f"Publish episode {a.date}"], cwd=repo)
    if not a.no_push:
        run(["git", "push", "origin", "main"], cwd=repo)
    print("Feed:", cfg["base_url"].rstrip("/") + "/feed.xml")
    print("Episode:", cfg["base_url"].rstrip("/") + "/episodes/" + fname)

if __name__ == "__main__":
    main()
