# KLOOM LO KADOSH // NOTHING IS HOLY

**Experimental Radio Archive.**
*The signal is the message. No gods, no masters.*

🔴 **[LIVE ARCHIVE](https://willbearfruits.github.io/kloom-radio/)**

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
- **Local audio** - Direct MP3/M4A playback
- Inline expandable players with autoplay

### ⌨️ Accessibility & Interaction
- Full keyboard navigation support
- ARIA labels for screen readers
- Focus indicators for keyboard users
- Lazy-loaded images for performance
- Reduced motion support

### 🔐 Production Security
- XSS prevention via DOM manipulation (no `innerHTML`)
- Content Security Policy (CSP) headers
- URL validation for iframe embeds
- Git LFS for large media files

### 🥚 Easter Eggs
- **IDDQD** - Type the Doom god mode cheat for a surprise
- Screen flash and title transformation

---

## Technology Stack

### Build System
- **Python 3.7+** - Static site generation
- **Jinja2** - Template engine
- **Pathlib** - Cross-platform path handling
- **urllib** - Mixcloud API integration

### Architecture
```
data/shows.json → generate.py → templates/ → output HTML
```

### Deployment
- **Git LFS** - Large audio file management
- **GitHub Pages** - Static hosting
- **GitHub Actions** - Automated deployment

---

## Local Development

### Prerequisites
```bash
python3 --version  # Requires 3.7+
pip install -r requirements.txt
```

### Build Site
```bash
python3 generate.py
```
This generates:
- `index.html` - Main archive page
- `shows/*.html` - Individual show pages

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
    "type": "embed",  // or "local_audio" or "youtube"
    "embed_url": "https://..."  // or "src": "./audio.m4a"
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

## Deployment Guide

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for comprehensive deployment instructions.

### Quick Deploy to GitHub Pages

1. **Build site**:
   ```bash
   python3 generate.py
   ```

2. **Commit changes**:
   ```bash
   git add .
   git commit -m "Update archive"
   git push origin master
   ```

3. **Configure GitHub Pages** (one-time setup):
   - Go to repository **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: **master** / **/ (root)**
   - Click **Save**

4. **Wait 2-5 minutes** for deployment

Your site will be live at: `https://willbearfruits.github.io/kloom-radio/`

---

## Project Structure

```
kloom-radio/
├── data/
│   └── shows.json              # Show database (single source of truth)
├── templates/
│   ├── index_list_glitch.html  # Main index template
│   ├── master_glitch.html      # Individual show page template
│   └── show_item_partial.html  # Show card component
├── shows/                      # Generated show pages
├── assets/
│   └── doom_iddqd.mp3         # Easter egg audio
├── *.m4a                       # Audio files (tracked with Git LFS)
├── index.html                  # Generated main page
├── 404.html                    # Custom 404 page
├── generate.py                 # Build script
├── requirements.txt            # Python dependencies
├── .gitattributes              # Git LFS configuration
└── .gitignore                  # Ignored files

Generated Files (committed to repo):
├── index.html
└── shows/*.html
```

---

## Troubleshooting

### GitHub Pages not deploying?
- Check **Settings → Pages** is enabled
- Verify branch is set to **master** and folder to **/ (root)**
- Check **Actions** tab for build errors
- Wait 5-10 minutes for first deployment

### Local audio not playing?
- Ensure audio file exists in repository root
- Check path in `shows.json` (should be `./filename.m4a`)
- For large files, ensure Git LFS is tracking: `git lfs ls-files`

### Build errors?
```bash
# Check Python version
python3 --version  # Should be 3.7+

# Reinstall dependencies
pip install -r requirements.txt

# Check data file syntax
python3 -m json.tool data/shows.json
```

### Player not working?
- Check browser console for CSP violations
- Verify URL is https://player-widget.mixcloud.com or https://www.youtube.com
- Test in different browser (Chrome, Firefox, Safari)

---

## Production Readiness

✅ **Security Score: 92/100**
- XSS vulnerabilities fixed
- Content Security Policy implemented
- URL validation for all embeds
- No hardcoded credentials

✅ **Accessibility Score: AA compliant**
- Keyboard navigation
- ARIA labels
- Focus indicators
- Screen reader support

✅ **Performance**
- Lazy-loaded images
- Inline CSS (no external requests)
- Git LFS for large media

See **[PRODUCTION_FIXES_SUMMARY.md](PRODUCTION_FIXES_SUMMARY.md)** for details.

---

## Credits

- **Host/Curator:** Yaniv Schonfeld
- **Infrastructure:** GitHub Pages
- **Code:** OpenClaw / MEZO Infrastructure
- **Production Fixes:** Claude Sonnet 4.5

---

## License

**Code:** MIT License (see [LICENSE](LICENSE))
**Audio Content:** Copyright their respective creators

---

**NOTHING IS HOLY.**
