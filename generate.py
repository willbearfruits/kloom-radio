import json
import os
import sys
import datetime
import urllib.request
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from urllib.parse import urlparse, parse_qs, unquote

# Config - Use relative paths
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / 'data' / 'shows.json'
TEMPLATE_DIR = BASE_DIR / 'templates'
OUTPUT_DIR = BASE_DIR
SHOWS_DIR = OUTPUT_DIR / 'shows'
BASE_URL  = 'https://willbearfruits.github.io/kloom-radio'

def load_data():
    """Load show data from JSON file with error handling."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at {DATA_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in data file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not load data: {e}")
        sys.exit(1)

def save_data(data):
    """Save show data to JSON file with error handling."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"ERROR: Could not save data: {e}")
        sys.exit(1)

def extract_feed_path(embed_url):
    parsed = urlparse(embed_url)
    query = parse_qs(parsed.query)
    if 'feed' in query:
        return unquote(query['feed'][0])
    return None

def fetch_mixcloud_metadata(feed_path):
    if not feed_path.endswith('/'):
        feed_path += '/'
    api_url = f"https://api.mixcloud.com{feed_path}"
    print(f"Fetching metadata from: {api_url}")
    try:
        with urllib.request.urlopen(api_url) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {api_url}: {e}")
        return None

def update_show_data(shows):
    updated = False
    for show in shows:
        if show['type'] == 'embed' and 'mixcloud' in show['embed_url']:
            if 'image_url' not in show or not show['image_url']:
                feed_path = extract_feed_path(show['embed_url'])
                if feed_path:
                    meta = fetch_mixcloud_metadata(feed_path)
                    if meta:
                        show['image_url'] = meta.get('pictures', {}).get('extra_large')
                        if not show.get('tags'):
                            show['tags'] = [t['name'] for t in meta.get('tags', [])]
                        if not show.get('description'):
                            show['description'] = meta.get('description', '')
                        show['play_count'] = meta.get('play_count', 0)
                        updated = True
    if updated:
        save_data(shows)
        print("Updated shows.json with new metadata.")
    return shows

def generate_og_image(show):
    """Generate a per-show OG image (1200x630 PNG)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("WARNING: Pillow not installed — skipping OG image generation")
        return

    W, H = 1200, 630
    BLUE, YELLOW, MAGENTA, GREEN, BLACK, WHITE = (
        (0,0,255), (255,255,0), (255,0,255), (0,255,0), (0,0,0), (255,255,255)
    )

    def load_font(size):
        for p in ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    def load_mono(size):
        for p in ["/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]:
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    img = Image.new("RGB", (W, H), BLUE)
    d   = ImageDraw.Draw(img)

    # scanlines
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 12), width=2)

    # border bars
    d.rectangle([0, 0, W, 8],   fill=BLACK)
    d.rectangle([0, H-8, W, H], fill=BLACK)
    d.rectangle([0, 0, 12, H],  fill=MAGENTA)
    d.rectangle([W-12, 0, W, H], fill=MAGENTA)

    # series label top-left
    d.rectangle([60, 60, 580, 108], fill=BLACK)
    d.text((80, 68), f"// {show.get('series','').upper()} // {show.get('date','')}", fill=YELLOW, font=load_mono(22))

    # main magenta box (shadow + fill + border)
    bx, by, bw, bh = 60, 140, 1080, 300
    d.rectangle([bx+6, by+6, bx+bw+6, by+bh+6], fill=BLACK)
    d.rectangle([bx, by, bx+bw, by+bh],          fill=MAGENTA)
    d.rectangle([bx, by, bx+bw, by+bh],          outline=BLACK, width=6)

    # --- title: wrap long titles across up to 3 lines ---
    title = show.get('title', 'UNTITLED')
    font_big  = load_font(72)
    font_med  = load_font(52)
    font_sm   = load_font(40)

    # measure and pick the right size / line-split
    def measure(txt, fnt):
        return d.textlength(txt, font=fnt)

    if measure(title, font_big) <= bw - 80:
        # fits on one line at big size
        d.text((600, 290), title, fill=BLACK, font=font_big, anchor="mm")
    elif measure(title, font_med) <= bw - 80:
        d.text((600, 290), title, fill=BLACK, font=font_med, anchor="mm")
    else:
        # split into words and wrap at med size
        words  = title.split()
        lines  = []
        current = ""
        for w in words:
            test = (current + " " + w).strip()
            if measure(test, font_med) <= bw - 80:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)

        # if still too many chars per line drop to small font
        fnt = font_med
        if any(measure(l, font_med) > bw - 80 for l in lines):
            fnt = font_sm
            # re-wrap at small size
            lines  = []
            current = ""
            for w in words:
                test = (current + " " + w).strip()
                if measure(test, fnt) <= bw - 80:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)

        line_h = fnt.size if hasattr(fnt, 'size') else 60
        total_h = line_h * len(lines)
        start_y = by + bh // 2 - total_h // 2 + line_h // 2
        for i, line in enumerate(lines[:3]):
            d.text((600, start_y + i * line_h), line, fill=BLACK, font=fnt, anchor="mm")

    # tags row
    tags = show.get('tags', [])[:4]
    tx = 100
    for tag in tags:
        tw = int(measure(f"#{tag}", load_mono(18))) + 24
        d.rectangle([tx, 478, tx+tw, 510], fill=WHITE, outline=BLACK, width=3)
        d.text((tx+12, 482), f"#{tag}", fill=BLACK, font=load_mono(18))
        tx += tw + 12

    # glitch bars top-right
    for i, (off, w, col) in enumerate([(0,240,YELLOW),(20,200,GREEN),(40,180,MAGENTA),(0,160,YELLOW)]):
        d.rectangle([900+off, 65+i*12, 900+off+w, 71+i*12], fill=col)

    # bottom status bar
    d.rectangle([0, 540, W, H-8], fill=BLACK)
    d.text((80, 558), "KLOOM LO KADOSH // NOTHING IS HOLY",  fill=GREEN,  font=load_mono(18))
    d.text((80, 585), "THE SIGNAL IS THE MESSAGE.",           fill=YELLOW, font=load_mono(15))

    # guest badge bottom-right if present
    guest = show.get('guest', '')
    if guest:
        d.rectangle([820, 548, 1130, 614], fill=YELLOW, outline=GREEN)
        d.text((975, 562), "GUEST",  fill=BLACK, font=load_mono(16), anchor="mm")
        d.text((975, 590), guest,    fill=BLACK, font=load_mono(20), anchor="mm")

    og_dir = BASE_DIR / 'assets' / 'og'
    og_dir.mkdir(parents=True, exist_ok=True)
    out = og_dir / f"{show['id']}.png"
    img.save(str(out), "PNG")
    print(f"Generated OG: assets/og/{show['id']}.png")


def tojson_filter(x):
    """Serialize to JSON, safe for HTML attributes (escapes < > & ')."""
    rv = json.dumps(x, ensure_ascii=False)
    rv = rv.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace("'", '\\u0027')
    return rv

def generate_search_index(shows):
    """Write client-side search index."""
    index = [{'id': s['id'], 'title': s.get('title',''),
              'description': s.get('description',''), 'series': s.get('series',''),
              'guest': s.get('guest',''), 'tags': s.get('tags',[])} for s in shows]
    with open(OUTPUT_DIR / 'search-index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)
    print("Generated: search-index.json")

def generate_rss_feed(shows):
    """Write RSS 2.0 feed."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')
    items = []
    for s in shows:
        try:
            dt = datetime.datetime.strptime(s['date'], '%Y-%m-%d')
            pub_date = dt.strftime('%a, %d %b %Y 00:00:00 +0000')
        except (ValueError, KeyError):
            pub_date = now
        desc = (s.get('description') or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        title_esc = (s.get('title') or 'Untitled').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        series_esc = (s.get('series') or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        items.append(
            f'    <item>\n'
            f'      <title>{title_esc}</title>\n'
            f'      <link>{BASE_URL}/shows/{s["id"]}.html</link>\n'
            f'      <description>{desc}</description>\n'
            f'      <pubDate>{pub_date}</pubDate>\n'
            f'      <category>{series_esc}</category>\n'
            f'      <guid isPermaLink="true">{BASE_URL}/shows/{s["id"]}.html</guid>\n'
            f'    </item>'
        )
    channel_items = '\n'.join(items)
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/Atom">\n'
        '  <channel>\n'
        '    <title>KLOOM LO KADOSH</title>\n'
        f'    <link>{BASE_URL}/</link>\n'
        '    <description>Nothing Is Holy. Experimental radio archive.</description>\n'
        f'    <lastBuildDate>{now}</lastBuildDate>\n'
        f'    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        + channel_items + '\n'
        '  </channel>\n'
        '</rss>\n'
    )
    with open(OUTPUT_DIR / 'feed.xml', 'w', encoding='utf-8') as f:
        f.write(rss)
    print("Generated: feed.xml")

def generate_sitemap(shows):
    """Write sitemap.xml."""
    urls = [
        f'  <url><loc>{BASE_URL}/</loc></url>',
        f'  <url><loc>{BASE_URL}/about.html</loc></url>',
        f'  <url><loc>{BASE_URL}/contact.html</loc></url>',
    ]
    for s in shows:
        urls.append(f'  <url><loc>{BASE_URL}/shows/{s["id"]}.html</loc><lastmod>{s["date"]}</lastmod></url>')
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls) + '\n'
        '</urlset>\n'
    )
    with open(OUTPUT_DIR / 'sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print("Generated: sitemap.xml")

def generate_robots_txt():
    """Write robots.txt with sitemap pointer."""
    with open(OUTPUT_DIR / 'robots.txt', 'w', encoding='utf-8') as f:
        f.write(f'User-agent: *\nDisallow:\n\nSitemap: {BASE_URL}/sitemap.xml\n')
    print("Generated: robots.txt")

def generate_site():
    """Generate static site from show data."""
    shows = load_data()
    shows = update_show_data(shows)
    shows.sort(key=lambda x: x['date'], reverse=True)

    # Setup Jinja Environment (Required for 'include')
    try:
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    except Exception as e:
        print(f"ERROR: Could not load templates from {TEMPLATE_DIR}: {e}")
        sys.exit(1)

    # Register tojson filter (HTML-attribute-safe JSON)
    env.filters['tojson'] = tojson_filter

    # Compute absolute URLs so the persistent player works across pages
    for show in shows:
        if show.get('src'):
            show['audio_url'] = BASE_URL + '/' + show['src'].replace('./', '')
        show['show_url'] = BASE_URL + '/shows/' + show['id'] + '.html'

    # 1. Generate Individual Show Pages
    try:
        master_template = env.get_template('master_glitch.html')
    except Exception as e:
        print(f"ERROR: Could not load master template: {e}")
        sys.exit(1)

    # Create shows directory if it doesn't exist
    try:
        SHOWS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Could not create shows directory: {e}")
        sys.exit(1)

    for show in shows:
        try:
            # Generate OG image for this show
            generate_og_image(show)

            context = show.copy()
            context['show']         = show          # full dict for tojson in templates
            context['BASE_URL']     = BASE_URL
            context['generated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output = master_template.render(context)
            filename = f"{show['id']}.html"
            filepath = SHOWS_DIR / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Generated Page: {filename}")
        except Exception as e:
            print(f"WARNING: Could not generate page for {show.get('id', 'unknown')}: {e}")

    # 2. Generate Index Page (List Layout)
    try:
        index_template = env.get_template('index_list_glitch.html')
        index_output = index_template.render(shows=shows, BASE_URL=BASE_URL, generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        with open(OUTPUT_DIR / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_output)
        print("Generated Index: index.html")
    except Exception as e:
        print(f"ERROR: Could not generate index page: {e}")
        sys.exit(1)

    # 3. Generate support files
    generate_search_index(shows)
    generate_rss_feed(shows)
    generate_sitemap(shows)
    generate_robots_txt()

    # 4. Generate static pages (about, contact)
    for page_name in ['about', 'contact']:
        try:
            tmpl = env.get_template(f'{page_name}.html')
            output = tmpl.render(BASE_URL=BASE_URL, generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            with open(OUTPUT_DIR / f'{page_name}.html', 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Generated: {page_name}.html")
        except Exception as e:
            print(f"WARNING: Could not generate {page_name}.html: {e}")

if __name__ == "__main__":
    generate_site()