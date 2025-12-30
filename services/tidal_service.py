import requests
import os
import base64
from fastapi import HTTPException
from models import SongMetadata

class TidalService:
    def __init__(self):
        self.auth_url = "https://auth.tidal.com/v1/oauth2/token"
        self.base_url = "https://openapi.tidal.com/v2"
        self.client_id = os.environ.get("TIDAL_CLIENT_ID")
        self.client_secret = os.environ.get("TIDAL_CLIENT_SECRET")
        self.token = None

    def _get_token(self) -> str:
        if not self.client_id or not self.client_secret:
             raise HTTPException(status_code=500, detail="TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET must be set")

        # Encode credentials
        creds = f"{self.client_id}:{self.client_secret}"
        b64_creds = base64.b64encode(creds.encode()).decode()

        headers = {
            "Authorization": f"Basic {b64_creds}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials"
        }

        try:
            resp = requests.post(self.auth_url, data=data, headers=headers)
            resp.raise_for_status()
            return resp.json()["access_token"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to authenticate with Tidal: {str(e)}")

    def get_metadata(self, url: str) -> SongMetadata:
        try:
            track_id = url.split("/")[-1]
            if not track_id.isdigit():
                 track_id = track_id.split("?")[0]
        except:
             raise HTTPException(status_code=400, detail="Invalid Tidal URL format")

        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.api+json" 
        }

        try:
            # V2 Endpoint with includes
            # Docs confirm 'albums' (plural) for include param
            api_url = f"{self.base_url}/tracks/{track_id}?countryCode=US&include=artists,albums"
            
            resp = requests.get(api_url, headers=headers)
            resp.raise_for_status()
            
            payload = resp.json()
            if "data" not in payload:
                 raise ValueError("Invalid API response format")
            
            data = payload["data"]
            attributes = data.get("attributes", {})
            relationships = data.get("relationships", {})
            included = payload.get("included", [])

            # Helper to find included resource
            def find_included(rtype, rid):
                for item in included:
                    if item.get("type") == rtype and item.get("id") == rid:
                        return item
                return None

            title = attributes.get("title", "Unknown Title")
            
            # Resolve Album
            album_name = "Unknown Album"
            if "albums" in relationships:
                # 'data' is array for to-many
                rel_data = relationships["albums"].get("data", [])
                if rel_data and len(rel_data) > 0:
                    album_obj = find_included("albums", rel_data[0]["id"])
                    if album_obj:
                         album_name = album_obj.get("attributes", {}).get("title", "Unknown Album")

            # Resolve Artist
            artist_name = "Unknown Artist"
            if "artists" in relationships:
                # 'data' is array for to-many
                rel_data = relationships["artists"].get("data", [])
                if rel_data and len(rel_data) > 0:
                    # Just take the first one
                    artist_obj = find_included("artists", rel_data[0]["id"])
                    if artist_obj:
                        artist_name = artist_obj.get("attributes", {}).get("name", "Unknown Artist")

            # Fallback if lookup failed but attributes has it (V2 sometimes denormalizes)
            if artist_name == "Unknown Artist" and "artistName" in attributes:
                 artist_name = attributes["artistName"]      
            if album_name == "Unknown Album" and "album" in attributes and isinstance(attributes["album"], str): # improbable in V2 but safe
                 album_name = attributes["album"]


            # Duration
            duration_iso = attributes.get("duration", "PT0S")
            duration_ms = self._parse_iso_duration(duration_iso)
            
            # Album Art - usually in album attributes 'imageLinks' or similar in V2? 
            # Or constructed: https://resources.tidal.com/images/{uuid}/origin.jpg
            # Let's check the album object for cover
            album_art_url = None
            # (Parsing album art logic is complex without seeing exact V2 structure for images, leaving null for now unless easy)

            return SongMetadata(
                title=title,
                artist=artist_name,
                album=album_name,
                duration_ms=duration_ms,
                tidal_url=url,
                album_art_url=album_art_url
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tidal API Error: {str(e)}")

    def _parse_iso_duration(self, duration_str: str) -> int:
        """Parses ISO 8601 duration (e.g. PT3M25S) to milliseconds"""
        import re
        match = re.search(r'PT(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return 0
        
        minutes = int(match.group(1) or 0)
        seconds = int(match.group(2) or 0)
        return (minutes * 60 + seconds) * 1000
