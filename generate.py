import json
import os
import datetime
import urllib.request
from jinja2 import Environment, FileSystemLoader
from urllib.parse import urlparse, parse_qs, unquote

# Config
DATA_FILE = '/home/glitches/clawd/kloom-radio/data/shows.json'
TEMPLATE_DIR = '/home/glitches/clawd/kloom-radio/templates'
OUTPUT_DIR = '/home/glitches/clawd/kloom-radio'
SHOWS_DIR = os.path.join(OUTPUT_DIR, 'shows')

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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
    shows = load_data()
    shows = update_show_data(shows)
    shows.sort(key=lambda x: x['date'], reverse=True)

    # Setup Jinja Environment (Required for 'include')
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    # 1. Generate Individual Show Pages
    master_template = env.get_template('master_glitch.html')
    
    if not os.path.exists(SHOWS_DIR):
        os.makedirs(SHOWS_DIR)

    for show in shows:
        context = show.copy()
        context['generated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output = master_template.render(context)
        filename = f"{show['id']}.html"
        filepath = os.path.join(SHOWS_DIR, filename)
        with open(filepath, 'w') as f:
            f.write(output)
        print(f"Generated Page: {filename}")

    # 2. Generate Index Page (List Layout)
    index_template = env.get_template('index_list_glitch.html')
    index_output = index_template.render(shows=shows, generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(index_output)
    print("Generated Index: index.html")

if __name__ == "__main__":
    generate_site()