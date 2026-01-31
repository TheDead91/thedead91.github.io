import json
import requests
import xml.etree.ElementTree as ET
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# 1. Setup credentials
JSON_PATH = ".github/workflows/service_account.json"
scopes = ["https://www.googleapis.com/auth/indexing"]
credentials = service_account.Credentials.from_service_account_file(JSON_PATH, scopes=scopes)
authed_session = AuthorizedSession(credentials)

# 2. Get all URLs from your sitemap
sitemap_url = "https://thedead91.github.io/sitemap.xml"
response = requests.get(sitemap_url)
root = ET.fromstring(response.content)
namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]

# 3. Ping Google for each URL
endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"

for url in urls:
    print(f"Pinging Google for: {url}")
    data = json.dumps({"url": url, "type": "URL_UPDATED"})
    response = authed_session.post(endpoint, data=data)
    
    if response.status_code == 200:
        print(f"✅ Success: {response.json()}")
    else:
        print(f"❌ Failed ({response.status_code}): {response.text}")