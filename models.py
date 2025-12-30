from pydantic import BaseModel, Field
from typing import Optional, List

# Spotify Metadata
class SongMetadata(BaseModel):
    title: str
    artist: str
    album: str
    duration_ms: int
    spotify_url: Optional[str] = None
    tidal_url: Optional[str] = None
    album_art_url: Optional[str] = None

# YouTube Search
class YouTubeSearchResult(BaseModel):
    video_id: str
    video_url: str
    title: str
    duration: int

# API Request/Response
class YouTubeSearchRequest(BaseModel):
    query: str

class YouTubeDownloadRequest(BaseModel):
    video_url: str = Field(..., alias="url")

class ConvertRequest(BaseModel):
    url: str

class TidalRequest(BaseModel):
    url: str

class ConvertResponse(BaseModel):
    metadata: SongMetadata
    youtube_url: str
    download_url: str  # URL to download the file
    filename: str
