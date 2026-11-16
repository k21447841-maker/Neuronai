from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.core.config import get_settings
from app.api.routes import (
    analytics_library, automation, media_animation, projects,
    providers, scripts, voice_audio, ws, youtube
)

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(title="NEUROFLOW AI API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def safe_global_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/health")
def health():
    return {"status": "ok", "service": "neuroflow-backend"}


app.include_router(projects.router)
app.include_router(providers.router)
app.include_router(scripts.router)
app.include_router(voice_audio.router)
app.include_router(media_animation.router)
app.include_router(youtube.router)
app.include_router(automation.router)
app.include_router(analytics_library.router)
app.include_router(ws.router)
