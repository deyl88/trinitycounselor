"""
Run this on your Mac:
  pip3 install httpx
  python3 fetch_tiktok.py
Then paste the output back into the chat.
"""
import httpx, json, time, random, sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_sec_uid(username: str) -> str:
    url = "https://www.tiktok.com/api/user/detail/"
    params = {"uniqueId": username, "aid": "1988", "app_language": "en", "app_name": "tiktok_web"}
    r = httpx.get(url, params=params, headers=HEADERS, follow_redirects=True, timeout=15)
    data = r.json()
    return data["userInfo"]["user"]["secUid"]

def fetch_videos(sec_uid: str, max_videos: int = 90) -> list:
    videos = []
    cursor = 0
    while len(videos) < max_videos:
        url = "https://www.tiktok.com/api/post/item_list/"
        params = {
            "secUid": sec_uid, "count": 30, "cursor": cursor,
            "aid": "1988", "app_language": "en", "app_name": "tiktok_web",
        }
        r = httpx.get(url, params=params, headers=HEADERS, follow_redirects=True, timeout=15)
        data = r.json()
        items = data.get("itemList", [])
        if not items:
            break
        for v in items:
            stats = v.get("stats", {})
            music = v.get("music", {})
            videos.append({
                "platform_video_id": v.get("id"),
                "title": v.get("desc", "")[:100],
                "caption": v.get("desc", ""),
                "duration_seconds": v.get("video", {}).get("duration"),
                "posted_at": v.get("createTime"),
                "views": stats.get("playCount", 0),
                "likes": stats.get("diggCount", 0),
                "comments": stats.get("commentCount", 0),
                "shares": stats.get("shareCount", 0),
                "song_name": music.get("title"),
                "song_artist": music.get("authorName"),
            })
        cursor = data.get("cursor", 0)
        if not data.get("hasMore"):
            break
        time.sleep(random.uniform(0.5, 1.0))
    return videos

if __name__ == "__main__":
    username = "summervictoria_music"
    print(f"Fetching {username}...", file=sys.stderr)
    try:
        sec_uid = get_sec_uid(username)
        print(f"secUid: {sec_uid}", file=sys.stderr)
        videos = fetch_videos(sec_uid)
        print(f"Fetched {len(videos)} videos", file=sys.stderr)
        print(json.dumps(videos, indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
