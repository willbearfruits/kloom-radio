# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & deploy

```bash
python3 generate.py          # rebuild everything into the repo root
python3 kloom_ssh.py [--port N]  # run the teletext SSH radio server (default port 2222)
git add . && git commit && git push origin master   # deploy (legacy GitHub Pages)
```

To connect to the SSH radio: `ssh -p 2222 localhost` (no auth required).
On a VPS, expose port 2222 and run `kloom_ssh.py` as a long-lived process.

No CI pipeline — GitHub Pages serves master at root directly. `.nojekyll` is present. Do not re-add a GitHub Actions workflow; the hosted runners on this account queue indefinitely.

## Architecture

`generate.py` is the entire build system. It:

1. Reads `data/shows.json` as the single source of truth for all show metadata.
2. Fetches missing Mixcloud thumbnails/tags via the Mixcloud API and writes them back to `shows.json`.
3. Computes `audio_url` (absolute) and `show_url` for each show so the persistent player works across pages.
4. Renders the active templates (index, master, about, contact) and writes output to the repo root or `shows/`. Legacy templates in `templates/` are not touched.
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

### SSH Teletext Radio (`kloom_ssh.py`)

A retro terminal-based radio interface accessible via SSH. Features:

- ASCII art logo with color cycling animation
- Boot sequence with static/noise effects
- Animated VU meters when a show is "tuned in"
- Full arrow-key navigation
- Shared "now playing" state across all connected sessions
- Live listener count and uptime display
- OSC 8 clickable hyperlinks (in supporting terminals)
- Help screen with keyboard reference

The server auto-generates an Ed25519 host key on first run (`.kloom_ssh_host_key`). This file is in `.gitignore` — never commit it.

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

## Easter eggs

The index page has a DOOM cheat code system. Type these anywhere (not in the search box):

| Code | Effect |
|---|---|
| `iddqd` | God Mode — yellow flash, glowing cards, HUD overlay, scanlines |
| `idkfa` | All Weapons — green flash, maxed ammo/armor, color cycling cards |
| `idclip` | No Clipping — cards become translucent and float |
| `idbehold` | Power Up — inverts colors, glitches all titles |
| `idmus` | Music Change — cycles through fake radio station names |
| `idspispopd` | Smashing Pumpkins — raining 🎃, sepia filter, screen shake |

The cheat system is defined in the `<script>` block in `index_list_glitch.html` as the `DOOM` object.

## Pitfalls

- `about.html` and `contact.html` in the repo root are **generated output**. Edit the templates in `templates/` — do not edit the root copies directly, they will be overwritten on the next `generate.py` run. (`404.html` is *not* generated — it is safe to edit in place.)
- `requirements.txt` lists `Jinja2==3.1.6` (build) and `asyncssh>=2.14` (SSH server). Pillow is an additional **soft dependency**: `generate_og_image()` lazy-imports it and prints a warning and skips OG generation if it is missing. Install it manually (`pip install Pillow`) if you need OG images to regenerate.
- Several templates in `templates/` (`1_terminal.html`, `2_white_cube.html`, `3_glitch.html`, `4_vhs.html`, `5_void.html`, `index_glitch.html`) are legacy/unused. `generate.py` does not reference them. Leave them alone.
- In `master_glitch.html`, the show dict is available as both top-level template variables *and* as `{{ show }}` (the full dict). The `show` variable is what you pass to `tojson` for `onclick` handlers — do not flatten it.
- `.kloom_ssh_host_key` is auto-generated and must never be committed. It's already in `.gitignore`.

## File layout notes

- `assets/player.css` + `assets/player.js` — persistent player + client-side search. Loaded on every page.
- `assets/og-image.png` — main site OG image (static). Per-show OG images are generated into `assets/og/`.
- `assets/favicon.svg` — site icon.
- Large audio files are tracked by Git LFS (`.gitattributes`).
- `assets/doom_iddqd.mp3` — easter egg audio triggered by the IDDQD cheat code.
- `kloom_ssh.py` — standalone SSH server for the teletext radio interface.

## Security notes

- CSP (Content-Security-Policy) is set on all pages via `<meta>` tag.
- `'unsafe-inline'` is required in `script-src` due to `onclick` handlers — this is an accepted trade-off.
- All user-facing URLs are validated (only Mixcloud, YouTube, or local paths allowed).
- The SSH server requires no authentication by design (it's a public radio).
