# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & deploy

```bash
python3 generate.py          # rebuild everything into the repo root
git add . && git commit && git push origin master   # deploy (legacy GitHub Pages)
```

No CI pipeline — GitHub Pages serves master at root directly. `.nojekyll` is present. Do not re-add a GitHub Actions workflow; the hosted runners on this account queue indefinitely.

## Architecture

`generate.py` is the entire build system. It:

1. Reads `data/shows.json` as the single source of truth for all show metadata.
2. Fetches missing Mixcloud thumbnails/tags via the Mixcloud API and writes them back to `shows.json`.
3. Computes `audio_url` (absolute) and `show_url` for each show so the persistent player works across pages.
4. Renders every Jinja2 template in `templates/` and writes output to the repo root or `shows/`.
5. Generates support files: `feed.xml` (RSS), `sitemap.xml`, `robots.txt`, `search-index.json`, and per-show OG images (`assets/og/*.png`) via Pillow.

### Template map

| Template | Output |
|---|---|
| `index_list_glitch.html` | `index.html` — main archive page |
| `master_glitch.html` | `shows/{id}.html` — individual show pages |
| `show_item_partial.html` | Included once per show inside the index |
| `player_partial.html` | Included in every page — the persistent player bar HTML |
| `about.html` | `about.html` |
| `contact.html` | `contact.html` |

### Show types & player behaviour

Shows in `shows.json` have a `type` field:

- **`local_audio`** — file hosted in the repo (`src` field). Plays through the persistent bottom-bar player (`KloomPlayer.load()`). Survives page navigation via `localStorage`; on restore a pulsing "TAP TO RESUME" hint appears because browsers block autoplay without a gesture.
- **`embed`** — Mixcloud iframe. Audio lives inside the iframe and cannot be routed through our `<Audio>` element. On the index, clicking play navigates to the show page (which renders the embed at full width). No cross-page persistence.
- **`youtube`** — YouTube iframe. Same constraints as embed.

### Key custom Jinja2 filter

`tojson` — registered in `generate.py` as `tojson_filter`. Serialises a Python dict to JSON and escapes `< > & '` so the output is safe inside HTML single-quoted attributes (used in `onclick='KloomPlayer.load(…)'`).

## Adding a new show

1. Add an entry to `data/shows.json`. Required fields: `id`, `title`, `series`, `date`, `tags` (array), `type`.
   - For local audio: `"type": "local_audio", "src": "./{filename}"`. Place the audio file in the repo root.
   - For Mixcloud: `"type": "embed", "embed_url": "https://player-widget.mixcloud.com/…"`. Image/tags are auto-fetched on next build if missing.
   - For YouTube: `"type": "youtube", "embed_url": "https://www.youtube.com/embed/{id}"`.
2. Run `python3 generate.py`.
3. Commit and push.

## Design constraints

The site uses a "Glitch Brutalist" aesthetic. CSS variables in `index_list_glitch.html`:

- `--bg: #0000ff` (BSOD blue)
- `--fg: #ffff00` (yellow)
- `--accent: #ff00ff` (magenta)
- `--highlight: #00ff00` (green)

Do not change the colour palette or the skew/shadow card style unless explicitly asked.

## File layout notes

- `assets/player.css` + `assets/player.js` — persistent player + client-side search. Loaded on every page.
- `assets/og-image.png` — main site OG image (static). Per-show OG images are generated into `assets/og/`.
- `assets/favicon.svg` — site icon.
- Large audio files are tracked by Git LFS (`.gitattributes`).
- `requirements.txt` lists `Jinja2` and `Pillow`.
