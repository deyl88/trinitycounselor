from fastapi import APIRouter, HTTPException
from models import EnrichmentRequest, EnrichmentResponse, EnrichmentData
from enrichment import enrich_song
import json

router = APIRouter()


@router.post("/", response_model=EnrichmentResponse)
def enrich(req: EnrichmentRequest):
    try:
        data = enrich_song(req.song_name, req.artist)
    except Exception as e:
        raise HTTPException(500, f"Enrichment failed: {e}")

    try:
        enrichment = EnrichmentData(**data)
    except Exception as e:
        raise HTTPException(500, f"Claude returned unexpected shape: {e}\nRaw: {data}")

    return EnrichmentResponse(
        song_name=req.song_name,
        artist=req.artist,
        enrichment=enrichment,
    )
