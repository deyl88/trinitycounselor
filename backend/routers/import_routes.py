from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from tiktok import fetch_all_videos
from song_parser import parse_song_from_tiktok

router = APIRouter()


class ManualVideo(BaseModel):
    song_name: str
    song_artist: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    posted_at: Optional[str] = None
    is_cover: int = 1
    is_original: int = 0
    caption: Optional[str] = None


class ManualImportRequest(BaseModel):
    videos: list[ManualVideo]


def _upsert_video(conn, platform: str, video_id: str, row: dict):
    conn.execute(
        """
        INSERT OR IGNORE INTO videos
            (platform, platform_video_id, title, caption, duration_seconds,
             posted_at, views, likes, comments, shares,
             song_name, song_artist, is_cover, is_original)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            platform,
            video_id,
            row["title"],
            row["caption"],
            row["duration_seconds"],
            row["posted_at"],
            row["views"],
            row["likes"],
            row["comments"],
            row["shares"],
            row["song_name"],
            row["song_artist"],
            row["is_cover"],
            row["is_original"],
        ),
    )


@router.post("/tiktok")
def import_tiktok():
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key='tiktok_access_token'"
        ).fetchone()

    if not row:
        raise HTTPException(
            400,
            "TikTok not connected. Visit /api/auth/tiktok/start to connect.",
        )

    access_token = row["value"]

    try:
        videos = fetch_all_videos(access_token)
    except Exception as e:
        raise HTTPException(502, f"TikTok API error: {e}")

    imported = skipped = 0

    with get_db() as conn:
        for v in videos:
            music = v.get("music_id") or {}
            song_data = parse_song_from_tiktok(
                title=v.get("title", ""),
                description=v.get("video_description", ""),
                music_title=music.get("title") if isinstance(music, dict) else None,
                music_author=music.get("author_name") if isinstance(music, dict) else None,
            )

            create_time = v.get("create_time")
            posted_at = (
                datetime.fromtimestamp(create_time, tz=timezone.utc).isoformat()
                if create_time
                else None
            )

            try:
                _upsert_video(conn, "tiktok", str(v["id"]), {
                    "title": v.get("title"),
                    "caption": v.get("video_description"),
                    "duration_seconds": v.get("duration"),
                    "posted_at": posted_at,
                    "views": v.get("view_count", 0),
                    "likes": v.get("like_count", 0),
                    "comments": v.get("comment_count", 0),
                    "shares": v.get("share_count", 0),
                    **song_data,
                })
                imported += 1
            except Exception:
                skipped += 1

    return {
        "status": "done",
        "platform": "tiktok",
        "imported": imported,
        "skipped": skipped,
        "total_fetched": len(videos),
    }


@router.post("/manual")
def import_manual(req: ManualImportRequest):
    imported = skipped = 0
    with get_db() as conn:
        for i, v in enumerate(req.videos):
            video_id = f"manual_{v.song_name}_{v.posted_at or i}".replace(" ", "_").lower()
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO videos
                       (platform, platform_video_id, song_name, song_artist,
                        views, likes, comments, shares, posted_at,
                        is_cover, is_original, caption)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    ("manual", video_id, v.song_name, v.song_artist,
                     v.views, v.likes, v.comments, v.shares, v.posted_at,
                     v.is_cover, v.is_original, v.caption),
                )
                imported += 1
            except Exception:
                skipped += 1
    return {"status": "done", "imported": imported, "skipped": skipped}


@router.get("/manual/count")
def manual_count():
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM videos WHERE platform='manual'"
        ).fetchone()[0]
    return {"videos_in_db": count}


@router.get("/tiktok/status")
def tiktok_import_status():
    with get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM videos WHERE platform='tiktok'"
        ).fetchone()[0]
        connected = conn.execute(
            "SELECT value FROM settings WHERE key='tiktok_access_token'"
        ).fetchone()
    return {
        "connected": connected is not None,
        "videos_in_db": count,
    }
