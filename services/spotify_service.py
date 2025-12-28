import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from models import SongMetadata
from fastapi import HTTPException

class SpotifyService:
    def __init__(self):
        client_id = os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            # We don't raise here to allow app startup, but methods will fail
            print("WARNING: Spotify credentials not found in environment.")
            self.sp = None
        else:
            self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            ))

    def get_metadata(self, spotify_url: str) -> SongMetadata:
        if not self.sp:
            raise HTTPException(status_code=500, detail="Spotify credentials not configured.")

        try:
            track = self.sp.track(spotify_url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid Spotify URL or API error: {str(e)}")

        artists = ", ".join([artist['name'] for artist in track['artists']])
        album_art = track['album']['images'][0]['url'] if track['album']['images'] else None

        return SongMetadata(
            title=track['name'],
            artist=artists,
            album=track['album']['name'],
            duration_ms=track['duration_ms'],
            spotify_url=track['external_urls']['spotify'],
            album_art_url=album_art
        )
