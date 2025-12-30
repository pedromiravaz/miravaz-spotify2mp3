import requests
import base64
import json

CLIENT_ID = "FZDirfhStba4BUgV"
CLIENT_SECRET = "J9zo75oL4JgoObWYhGphPnigyIo27IGFnrXDQpr4MrQ="

def get_token():
    auth_url = "https://auth.tidal.com/v1/oauth2/token"
    creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_creds = base64.b64encode(creds.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_creds}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    resp = requests.post(auth_url, data=data, headers=headers)
    resp.raise_for_status()
    return resp.json()["access_token"]

def debug_track():
    token = get_token()
    print(f"Token obtained.")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.api+json"
    }
    
    # Try fetching with includes
    track_id = "64975224"
    # Adding include parameters based on standard JSON:API patterns
    url = f"https://openapi.tidal.com/v2/tracks/{track_id}?countryCode=US&include=artists,album"
    
    print(f"Fetching: {url}")
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    debug_track()
