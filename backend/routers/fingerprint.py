from fastapi import APIRouter, HTTPException, BackgroundTasks
from fingerprint import build_fingerprint, get_latest_fingerprint

router = APIRouter()

_building = False


@router.post("/build")
def trigger_build(background_tasks: BackgroundTasks):
    """Kick off fingerprint build in the background."""
    global _building
    if _building:
        raise HTTPException(409, "Fingerprint build already in progress.")
    _building = True

    def _run():
        global _building
        try:
            build_fingerprint()
        finally:
            _building = False

    background_tasks.add_task(_run)
    return {"status": "building", "message": "Fingerprint build started. Poll /latest to check."}


@router.get("/latest")
def latest():
    fp = get_latest_fingerprint()
    if not fp:
        return {"status": "none", "message": "No fingerprint yet. POST /build first."}
    return {"status": "ok", "building": _building, "fingerprint": fp}


@router.get("/status")
def status():
    fp = get_latest_fingerprint()
    return {
        "building": _building,
        "has_fingerprint": fp is not None,
        "computed_at": fp.get("computed_at") if fp else None,
        "sample_size": fp.get("sample_size") if fp else None,
    }
