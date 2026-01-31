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

# 1. Load and Print "Before" History
seen_urls = set()
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        seen_urls = set(line.strip() for line in f if line.strip())
    print(f"📜 History before run: {len(seen_urls)} URLs indexed.")
    # Optional: print(sorted(list(seen_urls))) 
else:
    print("📜 No history file found. Starting fresh.")

# 2. Fetch Current Sitemap
response = requests.get(SITEMAP_URL)
root = ET.fromstring(response.content)
namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
all_urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]

# 3. Filter URLs
new_urls = [url for url in all_urls if url not in seen_urls and not any(b in url.lower() for b in BLOCKLIST)]

# 4. Auth & Ping
if not new_urls:
    print("✅ No new relevant pages to index.")
else:
    scopes = ["https://www.googleapis.com/auth/indexing"]
    credentials = service_account.Credentials.from_service_account_file(JSON_PATH, scopes=scopes)
    authed_session = AuthorizedSession(credentials)
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"

    print(f"🚀 Found {len(new_urls)} new pages. Pinging Google...")
    
    for url in new_urls:
        data = json.dumps({"url": url, "type": "URL_UPDATED"})
        resp = authed_session.post(endpoint, data=data)
        
        if resp.status_code == 200:
            print(f"✅ Success: {url}")
            seen_urls.add(url)
        elif resp.status_code == 429:
            print(f"🛑 Rate limit (429) reached. Stopping.")
            break
        else:
            print(f"❌ Failed ({resp.status_code}): {url}")
        time.sleep(1.5)

# 5. Save and Print "After" History
with open(HISTORY_FILE, "w") as f:
    for url in sorted(list(seen_urls)):
        f.write(f"{url}\n")
print(f"📝 History updated. Total URLs now indexed: {len(seen_urls)}")