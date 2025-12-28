from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# 1. Setup OpenTelemetry
resource = Resource.create(attributes={
    "service.name": "miravaz-spotify2mp3",
    "compose_service": "spotify2mp3"
})

tracer_provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)

import os

# 2. Initialize FastAPI
app = FastAPI(
    title="Miravaz Spotify2MP3",
    root_path=os.environ.get("ROOT_PATH", "")
)

# Middleware: Strip ROOT_PATH from incoming requests if present
@app.middleware("http")
async def strip_path_prefix(request: Request, call_next):
    root_path = os.environ.get("ROOT_PATH", "")
    if root_path and request.url.path.startswith(root_path):
        path = request.url.path[len(root_path):]
        if not path.startswith("/"):
            path = "/" + path
        request.scope["path"] = path
    response = await call_next(request)
    return response

from services.spotify_service import SpotifyService
from services.youtube_service import YouTubeService
from models import ConvertRequest, ConvertResponse, SongMetadata, YouTubeSearchResult

# 3. Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# --- Services ---
spotify_service = SpotifyService()
youtube_service = YouTubeService()

@app.get("/")
def health():
    return {
        "status": "online", 
        "service": "miravaz-spotify2mp3",
        "spotify_connected": spotify_service.sp is not None
    }

@app.post("/v1/spotify/meta", response_model=SongMetadata)
def get_spotify_metadata(request: ConvertRequest):
    return spotify_service.get_metadata(request.spotify_url)

@app.post("/v1/youtube/search", response_model=YouTubeSearchResult)
def search_youtube(query: str):
    return youtube_service.search_video(query)

@app.post("/v1/youtube/download")
def download_youtube_audio(video_url: str):
    filename, b64_data = youtube_service.download_to_base64(video_url)
    return {"filename": filename, "mp3_base64": b64_data}

@app.post("/v1/convert", response_model=ConvertResponse)
def convert_spotify_to_mp3(request: ConvertRequest):
    # 1. Get Metadata
    metadata = spotify_service.get_metadata(request.spotify_url)
    
    # 2. Search YouTube
    query = f"{metadata.artist} - {metadata.title} audio"
    yt_result = youtube_service.search_video(query)
    
    # 3. Download
    filename, b64_data = youtube_service.download_to_base64(yt_result.video_url)
    
    return ConvertResponse(
        metadata=metadata,
        youtube_url=yt_result.video_url,
        mp3_base64=b64_data,
        filename=filename
    )
