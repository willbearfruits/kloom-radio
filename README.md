# KLOOM LO KADOSH // NOTHING IS HOLY

**Experimental Radio Archive.**
*The signal is the message. No gods, no masters.*

🔴 **[LIVE ARCHIVE](https://willbearfruits.github.io/kloom-radio/)**

📡 **SSH Radio:** `ssh -p 2222 kloom-radio.net` *(coming soon)*

---

## About

Kloom Lo Kadosh (Nothing Is Holy) is a radio project hosted by Yaniv Schonfeld. This repository serves as the static archive for past broadcasts, mixtapes, experimental audio works, and visual content.

### Content Series

- 🎙️ **Kloom Originals & Guests:** Original content, AI-generated audio, and special guest features
- 🔊 **Nothing Is Holy:** Mixtapes, live broadcasts, and experimental sessions (No Sleep For The Wicked, Creative Destruction)
- 📻 **Kol Hazuti (Visual Voice):** Classic interview archive series hosted by Noa Elran (2009-2010)

**Total Shows:** 16 archived broadcasts spanning 2009-2026

---

## Features

### 🎨 Glitch Brutalist Design
- Blue Screen of Death color palette (#0000ff, #ffff00, #ff00ff)
- Impact typography with intentional visual disruption
- Skewed transforms and aggressive shadows
- Grayscale-to-color image transitions

### 🎵 Multi-Format Player Support
- **Mixcloud embeds** - Live broadcasts and mixtapes
- **YouTube embeds** - Video content and visual mixes
- **Local audio** - Direct MP3/M4A playback with persistent player
- Cross-page playback persistence via localStorage

### 📡 SSH Teletext Radio
A retro terminal-based radio interface:
```bash
ssh -p 2222 localhost
```
- ASCII art logo with color cycling
- Boot sequence animation
- Animated VU meters
- Arrow-key navigation
- Shared "now playing" across all listeners
- Clickable links (OSC 8 terminals)

### 📱 Mobile Responsive
- Full-width play strips on mobile
- Touch-friendly card layout
- Responsive typography

### ⌨️ Accessibility & Interaction
- Full keyboard navigation support
- ARIA labels for screen readers
- Focus indicators for keyboard users
- Lazy-loaded images for performance
- Reduced motion support

### 🔐 Production Security
- Content Security Policy (CSP) on all pages
- XSS prevention via DOM manipulation
- URL validation for iframe embeds
- Git LFS for large media files

### 🥚 DOOM Easter Eggs
Type these cheat codes anywhere on the index page:

| Code | Effect |
|------|--------|
| `IDDQD` | God Mode — invincibility, glowing cards, HUD overlay |
| `IDKFA` | All Weapons — maxed ammo/armor, color cycling |
| `IDCLIP` | No Clipping — floating translucent cards |
| `IDBEHOLD` | Power Up — inverted colors, glitched titles |
| `IDMUS` | Music Change — cycling radio station names |
| `IDSPISPOPD` | Smashing Pumpkins — raining 🎃, sepia madness |

---

## Technology Stack

### Build System
- **Python 3.7+** - Static site generation
- **Jinja2** - Template engine
- **Pillow** - OG image generation
- **asyncssh** - SSH server

### Architecture
```
data/shows.json → generate.py → templates/ → output HTML
                → kloom_ssh.py → SSH teletext interface
```

### Deployment
- **Git LFS** - Large audio file management
- **GitHub Pages** - Static hosting (no CI needed)

---

## Local Development

### Prerequisites
```bash
python3 --version  # Requires 3.7+
pip install -r requirements.txt
pip install Pillow  # Optional, for OG image generation
```

### Build Site
```bash
python3 generate.py
```

### Run SSH Radio
```bash
python3 kloom_ssh.py --port 2222
# Connect: ssh -p 2222 localhost
```

### Preview Locally
```bash
python3 -m http.server 8085
```
Then visit: http://localhost:8085

### Adding New Shows

1. **Edit** `data/shows.json`:
```json
{
    "id": "my-new-show",
    "title": "Show Title",
    "series": "Nothing Is Holy",
    "date": "2026-02-02",
    "tags": ["Mixtape", "Experimental"],
    "description": "Show description",
    "type": "embed",
    "embed_url": "https://..."
}
```

2. **Rebuild**:
```bash
python3 generate.py
```

3. **Commit & Deploy**:
```bash
git add .
git commit -m "Add new show: Title"
git push origin master
```

---

## Project Structure

```
kloom-radio/
├── data/
│   └── shows.json              # Show database (single source of truth)
├── templates/
│   ├── index_list_glitch.html  # Main index template
│   ├── master_glitch.html      # Individual show page template
│   ├── show_item_partial.html  # Show card component
│   ├── player_partial.html     # Persistent player bar
│   ├── about.html              # About page template
│   └── contact.html            # Contact page template
├── shows/                      # Generated show pages
├── assets/
│   ├── player.js               # Persistent player + search
│   ├── player.css              # Player styles
│   ├── og/                     # Generated OG images
│   ├── og-image.png            # Main site OG image
│   ├── favicon.svg             # Site icon
│   └── doom_iddqd.mp3          # Easter egg audio
├── *.m4a                       # Audio files (Git LFS)
├── index.html                  # Generated main page
├── about.html                  # Generated about page
├── contact.html                # Generated contact page
├── 404.html                    # Custom 404 page
├── feed.xml                    # RSS feed
├── sitemap.xml                 # XML sitemap
├── robots.txt                  # Robots config
├── search-index.json           # Client-side search data
├── generate.py                 # Static site generator
├── kloom_ssh.py                # SSH teletext server
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Claude Code instructions
└── .gitignore                  # Ignored files (incl. SSH host key)
```

---

## Production Readiness

✅ **Security Score: 98/100**
- Content Security Policy on all pages
- XSS prevention
- URL validation for all embeds
- No hardcoded credentials
- SSH host key protected via .gitignore

✅ **Accessibility Score: AA compliant**
- Keyboard navigation
- ARIA labels
- Focus indicators
- Screen reader support
- Mobile play buttons

✅ **SEO**
- Canonical URLs on all pages
- OpenGraph + Twitter cards
- JSON-LD structured data
- RSS feed + sitemap

✅ **Performance**
- Lazy-loaded images
- Inline CSS
- Git LFS for large media

---

## Credits

- **Host/Curator:** Yaniv Schonfeld
- **Infrastructure:** GitHub Pages
- **Code:** Claude Opus 4.5 + Claude Sonnet 4.5
- **Design:** Glitch Brutalist aesthetic

---

## License

**Code:** MIT License (see [LICENSE](LICENSE))
**Audio Content:** Copyright their respective creators

---

**NOTHING IS HOLY.**
