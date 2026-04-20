from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router,          prefix="/api/videos",         tags=["videos"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(settings_router.router,   prefix="/api/settings",      tags=["settings"])
app.include_router(enrichment_router.router, prefix="/api/enrich",        tags=["enrichment"])
app.include_router(auth_router.router,       prefix="/api/auth",           tags=["auth"])
app.include_router(import_routes.router,     prefix="/api/import",         tags=["import"])
app.include_router(fingerprint_router.router, prefix="/api/fingerprint",   tags=["fingerprint"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "sv-studio"}
