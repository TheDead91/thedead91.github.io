import json
import requests
from oauth2client.service_account import ServiceAccountCredentials
import xml.etree.ElementTree as ET

# 1. Setup credentials
scope = ["https://www.googleapis.com/auth/indexing"]
with open(".github/workflows/service_account.json", "r") as f:
    key_data = json.load(f)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(key_data, scope)

# 2. Get all URLs from your sitemap
sitemap_url = "https://thedead91.github.io/sitemap.xml"
response = requests.get(sitemap_url)
root = ET.fromstring(response.content)
# Handle namespaces usually found in sitemaps
namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = [url.find('ns:loc', namespace).text for url in root.findall('ns:url', namespace)]

# 3. Ping Google for each URL
endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
for url in urls:
    print(f"Pinging Google for: {url}")
    http_auth = credentials.authorize(requests.Session())
    data = json.dumps({"url": url, "type": "URL_UPDATED"})
    result = http_auth.post(endpoint, data=data)
    print(result.json())