import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from database import init_db
from routers import (
    videos,
    recommendations,
    settings as settings_router,
    enrichment as enrichment_router,
    auth as auth_router,
    import_routes,
    fingerprint as fingerprint_router,
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SV Studio",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router,             prefix="/api/videos",         tags=["videos"])
app.include_router(recommendations.router,    prefix="/api/recommendations", tags=["recommendations"])
app.include_router(settings_router.router,    prefix="/api/settings",        tags=["settings"])
app.include_router(enrichment_router.router,  prefix="/api/enrich",          tags=["enrichment"])
app.include_router(auth_router.router,        prefix="/api/auth",            tags=["auth"])
app.include_router(import_routes.router,      prefix="/api/import",          tags=["import"])
app.include_router(fingerprint_router.router, prefix="/api/fingerprint",     tags=["fingerprint"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "sv-studio"}


# Serve React SPA — only active in production when static/ dir is present
if os.path.isdir(_STATIC_DIR):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        candidate = os.path.join(_STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
