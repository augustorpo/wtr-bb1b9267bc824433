# Adam and Eve FM — private Apple Podcasts feed

**Show:** Adam and Eve FM (Adam (bull) vs Eve (skeptic))
**GitHub account:** augustorpo (free plan → **public** repo with unguessable name)
**Repo:** https://github.com/augustorpo/wtr-bb1b9267bc824433
**Feed URL (subscribe in Apple Podcasts / any podcast app):**
https://augustorpo.github.io/wtr-bb1b9267bc824433/feed.xml

`<itunes:block>Yes</itunes:block>` keeps it out of the public Apple directory; anyone with the URL can still subscribe.

**Description:** Adam (bull) and Eve (skeptic) debate markets, theses, articles and big ideas, casual and fun.
**Cover:** `cover-v3.jpg` (3000×3000 JPG, bull art; `cover.jpg` is a copy). Set via `"cover"` in config.json (publisher default is also `cover-v3.jpg`).

## One-command weekly publish

```bash
python3 /home/box/podcast/publish_episode.py \
  --mp3 /workspace/weekly-audio-YYYY-MM-DD/weekly-thesis-review.mp3 \
  --date YYYY-MM-DD \
  --chapters /workspace/weekly-audio-YYYY-MM-DD/chapters.json
```

Optional flags: `--title`, `--description`, `--pubdate "YYYY-MM-DD HH:MM"` (America/New_York), `--replace`, `--no-push`.

Config: `/home/box/podcast/config.json` (repo, base_url, clone path).
The script copies the MP3 into `episodes/`, updates `episodes.json`, regenerates `feed.xml` with the Adam and Eve FM branding, commits, and pushes to `main` (GitHub Pages).

## One-off / special episodes

Specials are keyed by `--slug` so they never collide with (or replace) the weekly episode for the same date:

```bash
python3 /home/box/podcast/publish_episode.py \
  --mp3 /workspace/hims-2026-09-28/hims-isnt-telemedicine-2026-09-28.mp3 \
  --date 2026-09-28 --slug 2026-09-28-hims-no-es-telemedicina \
  --title "HIMS Isn't Telemedicine — Adan vs Eve (Special)" \
  --description-file /workspace/hims-2026-09-28/show-notes.txt \
  --chapters /workspace/hims-2026-09-28/chapters.json --append-chapters
```

- File: `episodes/<slug>.mp3`, guid: `<slug>`. Without `--slug`, behavior is unchanged (`<date>-weekly-thesis-review`, guid `weekly-thesis-review-<date>`).
- New flags: `--slug`, `--description-file`, `--append-chapters`, `--episode-type full|bonus|trailer` (default full).
- `--replace` now replaces the entry with the same slug (= same date for weekly episodes). The MP3 is copied only after the duplicate check passes.

## Specials published
- 2026-09-28 — HIMS Isn't Telemedicine — Adan vs Eve (Special). Source: `/workspace/hims-2026-09-28/`

## Episode 1 render (box)

Source: `/workspace/weekly-audio-2026-09-28/`
Re-render: `rm -rf segments && .venv/bin/python render.py`
Hosts: Adan=en-US-AndrewNeural, Eve=en-US-AvaNeural.
