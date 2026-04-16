from fastapi import APIRouter, HTTPException
from database import get_db
from models import RecommendationCreate, RecommendationResponse, RecommendationUpdate
from typing import List, Optional

router = APIRouter()

_ALLOWED_STATUSES = {"pending", "saved", "skipped"}


@router.get("/", response_model=List[RecommendationResponse])
def list_recommendations(status: Optional[str] = None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM recommendations WHERE status=? ORDER BY final_score DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM recommendations ORDER BY final_score DESC"
            ).fetchall()
        return [dict(r) for r in rows]


@router.post("/", response_model=RecommendationResponse, status_code=201)
def create_recommendation(rec: RecommendationCreate):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO recommendations
               (song_name, song_artist, trending_score, style_fit_score,
                final_score, tip_text, status)
               VALUES (?,?,?,?,?,?,?)""",
            (rec.song_name, rec.song_artist, rec.trending_score,
             rec.style_fit_score, rec.final_score, rec.tip_text, rec.status),
        )
        row = conn.execute(
            "SELECT * FROM recommendations WHERE id=?", (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


@router.patch("/{rec_id}", response_model=RecommendationResponse)
def update_status(rec_id: int, update: RecommendationUpdate):
    if update.status not in _ALLOWED_STATUSES:
        raise HTTPException(400, f"status must be one of {_ALLOWED_STATUSES}")
    with get_db() as conn:
        conn.execute(
            "UPDATE recommendations SET status=? WHERE id=?", (update.status, rec_id)
        )
        row = conn.execute(
            "SELECT * FROM recommendations WHERE id=?", (rec_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Recommendation not found")
        return dict(row)
