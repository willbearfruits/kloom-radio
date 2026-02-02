# KLOOM RADIO ARCHIVE - DEPLOYMENT GUIDE

## GitHub Pages Deployment

### Prerequisites
1. Python 3.7+
2. Git LFS installed
3. GitHub account

### Setup Instructions

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Generate Site
```bash
python3 generate.py
```

#### 3. Configure Git LFS (for large audio files)
```bash
git lfs install
git lfs track "*.m4a"
git add .gitattributes
```

#### 4. Commit and Push
```bash
git add .
git commit -m "Deploy: Production-ready build"
git push origin master
```

#### 5. Configure GitHub Pages
1. Go to repository Settings
2. Navigate to Pages section
3. Set Source to: **Deploy from branch**
4. Select branch: **master**
5. Select folder: **/ (root)**
6. Click Save

#### 6. Verify Deployment
Your site will be available at:
```
https://willbearfruits.github.io/kloom-radio/
```

### Build Process

The `generate.py` script:
- Reads show data from `data/shows.json`
- Fetches metadata from Mixcloud API (if needed)
- Generates individual show pages in `shows/`
- Generates main index page `index.html`

### Directory Structure
```
kloom-radio/
├── data/
│   └── shows.json          # Show data (single source of truth)
├── templates/
│   ├── index_list_glitch.html
│   ├── master_glitch.html
│   └── show_item_partial.html
├── shows/                  # Generated show pages
├── assets/                 # Static assets
├── index.html             # Generated index page
├── 404.html               # Custom 404 page
├── generate.py            # Build script
└── requirements.txt       # Python dependencies
```

### Updating Content

To add new shows:
1. Edit `data/shows.json`
2. Run `python3 generate.py`
3. Commit and push changes

### Troubleshooting

**Large files rejected by GitHub:**
- Make sure Git LFS is installed and tracking audio files
- Check `.gitattributes` file exists
- Use `git lfs ls-files` to verify LFS tracking

**404 errors on deployment:**
- Verify GitHub Pages is enabled
- Check that source is set to master branch, root folder
- Allow 5-10 minutes for initial deployment

**Audio player not working:**
- Check browser console for CSP violations
- Verify audio file paths are correct
- For local testing, use `python3 -m http.server 8000`

### Security Notes
- XSS vulnerabilities fixed (DOM manipulation instead of innerHTML)
- Content Security Policy implemented
- ARIA labels for accessibility
- Keyboard navigation support

### Performance Optimizations
- Lazy loading for images
- Inline CSS for reduced requests
- Git LFS for large media files
- Grayscale images with color on hover (reduces processing)

---

**NOTHING IS HOLY. DEPLOY WITH CONFIDENCE.**
