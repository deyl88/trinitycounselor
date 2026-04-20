import re

_ORIGINAL_MARKERS = [
    "original sound", "original audio", "my original",
    "i wrote this", "wrote this song", "my song", "original song",
]

# Patterns like "cover of Blank Space by Taylor Swift"
_COVER_RE = re.compile(
    r"cover of ['\"']?(.+?)['\"']?\s+by\s+([^\n#|]+)", re.IGNORECASE
)
# Patterns like "Blank Space - Taylor Swift (cover)"
_DASH_RE = re.compile(
    r"^['\"']?(.+?)['\"']?\s*[-\u2013]\s*(.+?)\s*(?:\(cover\))?$", re.IGNORECASE
)


def parse_song_from_tiktok(
    title: str = "",
    description: str = "",
    music_title: str = None,
    music_author: str = None,
) -> dict:
    """
    Return dict with song_name, song_artist, is_cover, is_original.
    Priority: explicit cover pattern in text > TikTok music metadata > title parse.
    """
    full_text = f"{title or ''} {description or ''}".strip()
    lower = full_text.lower()

    is_original = any(m in lower for m in _ORIGINAL_MARKERS) or (
        bool(re.search(r"\boriginal\b", lower)) and "originally by" not in lower
    )

    song_name = None
    artist = None

    # 1. Explicit "cover of X by Y" in caption
    match = _COVER_RE.search(full_text)
    if match:
        song_name = match.group(1).strip().strip("\"'")
        artist = match.group(2).strip().strip("\"'.,")

    # 2. TikTok music metadata (most reliable when present)
    if not song_name and music_title:
        song_name = music_title.strip()
        artist = music_author.strip() if music_author else None

    # 3. "Song - Artist" pattern in title
    if not song_name and title:
        m = _DASH_RE.match(title.strip())
        if m:
            song_name = m.group(1).strip().strip("\"'")
            artist = m.group(2).strip().strip("\"'.,")

    return {
        "song_name": song_name,
        "song_artist": artist,
        "is_cover": 0 if is_original else 1,
        "is_original": 1 if is_original else 0,
    }


def parse_song_from_instagram(caption: str = "") -> dict:
    """Same logic but Instagram captions tend to be more explicit."""
    return parse_song_from_tiktok(description=caption)
