from fastapi import APIRouter, HTTPException
from database import get_db
from models import VideoCreate, VideoResponse
from typing import List

router = APIRouter()


@router.get("/", response_model=List[VideoResponse])
def list_videos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM videos ORDER BY posted_at DESC").fetchall()
        return [dict(r) for r in rows]


@router.post("/", response_model=VideoResponse, status_code=201)
def create_video(video: VideoCreate):
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO videos
               (platform, platform_video_id, title, caption, duration_seconds,
                posted_at, views, likes, comments, shares, saves, follower_gain,
                song_name, song_artist, is_cover, is_original, enrichment_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (video.platform, video.platform_video_id, video.title, video.caption,
             video.duration_seconds, video.posted_at, video.views, video.likes,
             video.comments, video.shares, video.saves, video.follower_gain,
             video.song_name, video.song_artist, video.is_cover, video.is_original,
             video.enrichment_json),
        )
        row = conn.execute("SELECT * FROM videos WHERE id=?", (cursor.lastrowid,)).fetchone()
        return dict(row)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id=?", (video_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Video not found")
        return dict(row)


@router.delete("/{video_id}", status_code=204)
def delete_video(video_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM videos WHERE id=?", (video_id,))
