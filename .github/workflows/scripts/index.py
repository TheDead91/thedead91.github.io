import json
import os
import time
import requests
import xml.etree.ElementTree as ET
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Config
JSON_PATH = ".github/workflows/service_account.json"
SITEMAP_URL = "https://thedead91.github.io/sitemap.xml"
HISTORY_FILE = "indexed_urls.txt"
BLOCKLIST = ["google", "page", "archives"]

def ping_google(session, url, type):
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    data = json.dumps({"url": url, "type": type})
    resp = session.post(endpoint, data=data)
    if resp.status_code == 200:
        print(f"✅ {type}: {url}")
        return True
    elif resp.status_code == 429:
        print(f"🛑 Rate limit hit (429).")
        return "REACHED_LIMIT"
    else:
        print(f"❌ Failed {type} ({resp.status_code}): {url}")
        return False

# 1. Load History
seen_urls = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        seen_urls = set(line.strip() for line in f if line.strip())
print(f"📜 History: {len(seen_urls)} URLs previously indexed --> {seen_urls}")

# 2. Fetch Current Sitemap
response = requests.get(SITEMAP_URL)
root = ET.fromstring(response.content)
namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
current_urls = set(url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace))

# 3. Logic: Find New vs Removed
new_to_index = [u for u in current_urls if u not in seen_urls and not any(b in u.lower() for b in BLOCKLIST)]
removed_to_deindex = [u for u in seen_urls if u not in current_urls]

# 4. Auth & Ping
if not new_to_index and not removed_to_deindex:
    print("✅ Everything is already in sync.")
else:
    scopes = ["https://www.googleapis.com/auth/indexing"]
    credentials = service_account.Credentials.from_service_account_file(JSON_PATH, scopes=scopes)
    authed_session = AuthorizedSession(credentials)

    # Process Deletions First (Google prioritizes cleaning up dead links)
    if removed_to_deindex:
        print(f"🗑️ Found {len(removed_to_deindex)} removed pages. Requesting de-indexing...")
        for url in removed_to_deindex:
            res = ping_google(authed_session, url, "URL_DELETED")
            if res == "REACHED_LIMIT": break
            if res: seen_urls.remove(url)
            time.sleep(1.5)

    # Process New Content
    if new_to_index:
        print(f"🚀 Found {len(new_to_index)} new pages. Requesting indexing...")
        for url in new_to_index:
            res = ping_google(authed_session, url, "URL_UPDATED")
            if res == "REACHED_LIMIT": break
            if res: seen_urls.add(url)
            time.sleep(1.5)

# 5. Save History
with open(HISTORY_FILE, "w") as f:
    for url in sorted(list(seen_urls)):
        f.write(f"{url}\n")
print(f"📝 Sync complete. History now at {len(seen_urls)} URLs --> {seen_urls}")