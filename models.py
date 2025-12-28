from pydantic import BaseModel, Field
from typing import Optional, List

# Spotify Metadata
class SongMetadata(BaseModel):
    title: str
    artist: str

    album: str
    duration_ms: int
    spotify_url: str
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
    spotify_url: str = Field(..., alias="url")

class ConvertResponse(BaseModel):
    metadata: SongMetadata
    youtube_url: str
    mp3_base64: str  # The actual file content
    filename: str
