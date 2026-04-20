import os
import httpx
from urllib.parse import urlencode

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"

VIDEO_FIELDS = "id,title,video_description,duration,create_time,like_count,comment_count,share_count,view_count,music_id"


def get_auth_url(redirect_uri: str, state: str = "svstudio") -> str:
    params = {
        "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
        "response_type": "code",
        "scope": "user.info.basic,video.list",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return TIKTOK_AUTH_URL + "?" + urlencode(params)


def exchange_code(code: str, redirect_uri: str) -> dict:
    resp = httpx.post(TIKTOK_TOKEN_URL, data={
        "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
        "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_all_videos(access_token: str) -> list[dict]:
    """Paginate through all videos using TikTok cursor pagination."""
    videos = []
    cursor = 0
    has_more = True

    while has_more:
        resp = httpx.post(
            TIKTOK_VIDEO_LIST_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": VIDEO_FIELDS},
            json={"max_count": 20, "cursor": cursor},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        batch = data.get("videos", [])
        videos.extend(batch)
        has_more = data.get("has_more", False)
        cursor = data.get("cursor", 0)
        if not batch:
            break

    return videos
