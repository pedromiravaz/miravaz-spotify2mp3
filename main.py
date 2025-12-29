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
from models import ConvertRequest, ConvertResponse, SongMetadata, YouTubeSearchResult, YouTubeSearchRequest, YouTubeDownloadRequest

from fastapi.staticfiles import StaticFiles

# ... previous code ...

# 3. Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Mount downloads directory
os.makedirs("/app/downloads", exist_ok=True)
app.mount("/downloads", StaticFiles(directory="/app/downloads"), name="downloads")

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
def search_youtube(request: YouTubeSearchRequest):
    return youtube_service.search_video(request.query)

@app.post("/v1/youtube/download")
def download_youtube_audio(request: YouTubeDownloadRequest):
    # For direct download, we use a generic name or parse from video title if available
    # Here we just use video ID as base
    filename = youtube_service.download_file(request.video_url, "downloaded_audio")
    return {"filename": filename, "download_url": f"/downloads/{filename}"}

@app.post("/v1/convert", response_model=ConvertResponse)
def convert_spotify_to_mp3(request: ConvertRequest, req: Request):
    # 1. Get Metadata
    metadata = spotify_service.get_metadata(request.spotify_url)
    
    # 2. Search YouTube
    query = f"{metadata.artist} - {metadata.title} audio"
    yt_result = youtube_service.search_video(query)
    
    # 3. Download
    filename_base = f"{metadata.artist} - {metadata.title}"
    filename = youtube_service.download_file(yt_result.video_url, filename_base)
    
    # Construct external absolute URL
    scheme = req.url.scheme
    host = req.headers.get("host", "localhost")
    root_path = os.environ.get("ROOT_PATH", "")
    
    # Ensure root_path formats correctly (no trailing slash, leading slash handled by join or f-string logic)
    if root_path and not root_path.startswith("/"):
        root_path = "/" + root_path
    if root_path and root_path.endswith("/"):
        root_path = root_path[:-1]

    download_url = f"{scheme}://{host}{root_path}/downloads/{filename}"

    return ConvertResponse(
        metadata=metadata,
        youtube_url=yt_result.video_url,
        download_url=download_url,
        filename=filename
    )
