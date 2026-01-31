import json
import os
import requests
import xml.etree.ElementTree as ET
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# Config
JSON_PATH = ".github/workflows/service_account.json"
SITEMAP_URL = "https://thedead91.github.io/sitemap.xml"
HISTORY_FILE = "indexed_urls.txt"

# 1. Load History
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        seen_urls = set(line.strip() for line in f if line.strip())
else:
    seen_urls = set()

# 2. Fetch Current Sitemap
response = requests.get(SITEMAP_URL)
root = ET.fromstring(response.content)
namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
current_urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]

# 3. Find Truly New URLs
new_urls = [url for url in current_urls if url not in seen_urls]

# 4. Auth & Ping Google
if not new_urls:
    print("✅ No new pages detected.")
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
        else:
            print(f"❌ Failed ({resp.status_code}): {url}")

    # 5. Save updated history
    with open(HISTORY_FILE, "w") as f:
        for url in set(list(seen_urls) + current_urls):
            f.write(f"{url}\n")