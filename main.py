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

# 3. Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
def health():
    return {"status": "online", "service": "miravaz-spotify2mp3"}
