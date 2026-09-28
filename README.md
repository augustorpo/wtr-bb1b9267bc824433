# Weekly Thesis Review — private Apple Podcasts feed

**Show:** Weekly Thesis Review (Adan (bull) vs Eve (skeptic), Bull vs Skeptic FM)
**GitHub account:** augustorpo (free plan → **public** repo with unguessable name)
**Repo:** https://github.com/augustorpo/wtr-bb1b9267bc824433
**Feed URL (subscribe in Apple Podcasts / any podcast app):**
https://augustorpo.github.io/wtr-bb1b9267bc824433/feed.xml

`<itunes:block>Yes</itunes:block>` keeps it out of the public Apple directory; anyone with the URL can still subscribe.

## One-command weekly publish

```bash
python3 /home/box/podcast/publish_episode.py \
  --mp3 /workspace/weekly-audio-YYYY-MM-DD/weekly-thesis-review.mp3 \
  --date YYYY-MM-DD \
  --chapters /workspace/weekly-audio-YYYY-MM-DD/chapters.json
```

Optional flags: `--title`, `--description`, `--pubdate "YYYY-MM-DD HH:MM"` (America/New_York), `--replace`, `--no-push`.

Config: `/home/box/podcast/config.json` (repo, base_url, clone path).
The script copies the MP3 into `episodes/`, updates `episodes.json`, regenerates `feed.xml`, commits, and pushes to `main` (GitHub Pages).

## Episode 1 render (box)

Source: `/workspace/weekly-audio-2026-09-28/`
Re-render: `rm -rf segments && .venv/bin/python render.py`
Hosts: Adan=en-US-AndrewNeural, Eve=en-US-AvaNeural.
