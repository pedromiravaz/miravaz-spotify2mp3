import requests
import json
import re

URL = "https://tidal.com/browse/track/64975224"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://tidal.com/',
}

try:
    print(f"Fetching {URL}...")
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    html = response.text
    print("Success! Length:", len(html))
    
    # Simple regex extraction for OpenGraph tags
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    type_match = re.search(r'<meta property="og:type" content="([^"]+)"', html)
    
    # Tidal specific: "Artist - Title" or just "Title"?
    # Often title is "Track Name - Artist"
    
    title = title_match.group(1) if title_match else "Metadata Not Found"
    print("og:title:", title)
    print("og:image:", image_match.group(1) if image_match else "No Image")
    
    # Trying to find Album
    # <meta property="og:audio:album" content="..."> might exist
    album_match = re.search(r'<meta property="og:audio:album" content="([^"]+)"', html)
    print("album:", album_match.group(1) if album_match else "Not found")

except Exception as e:
    print("Error:", e)
    if 'response' in locals():
        print("Status Code:", response.status_code)
