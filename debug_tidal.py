import requests
import os
import base64
import json

# User provided (simulated here for debug, in real usage use env vars)
CLIENT_ID = os.environ.get("TIDAL_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TIDAL_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Please set TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET env vars")
    exit(1)

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

def debug_api():
    try:
        token = get_token()
        print(f"Auth Successful. Token: {token[:10]}...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.tidal.v1+json"
        }
        
        # 1. Try to Search (to verify catalog access)
        # Endpoint: https://openapi.tidal.com/v2/searchresults/tracks?query=test&countryCode=US
        search_url = "https://openapi.tidal.com/v2/searchresults/tracks?query=Bruce%20Springsteen&countryCode=US&limit=1"
        print(f"\nTesting Search: {search_url}")
        resp = requests.get(search_url, headers=headers)
        if resp.status_code == 200:
            print("Search OK!")
            data = resp.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Search Failed: {resp.status_code}")
            print(resp.text)

        # 2. Try the specific track
        track_id = "64975224"
        track_url = f"https://openapi.tidal.com/v2/tracks/{track_id}?countryCode=US"
        print(f"\nTesting Track Fetch: {track_url}")
        resp = requests.get(track_url, headers=headers)
        if resp.status_code == 200:
            print("Track Fetch OK!")
            print(json.dumps(resp.json(), indent=2))
        else:
            print(f"Track Fetch Failed: {resp.status_code}")
            print(resp.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api()
