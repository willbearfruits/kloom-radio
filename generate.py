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
            context = show.copy()
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
        index_output = index_template.render(shows=shows, generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        with open(OUTPUT_DIR / 'index.html', 'w', encoding='utf-8') as f:
            f.write(index_output)
        print("Generated Index: index.html")
    except Exception as e:
        print(f"ERROR: Could not generate index page: {e}")
        sys.exit(1)

if __name__ == "__main__":
    generate_site()