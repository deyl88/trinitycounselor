"""
Style Fingerprint Engine

Analyzes Summer's top-performing videos to build a taste profile.
Top 20% by engagement score are enriched via Claude, then aggregated
into a fingerprint stored in the style_fingerprint table.
"""

import json
import math
from collections import Counter
from database import get_db
from enrichment import enrich_song


def _engagement_score(v: dict) -> float:
    """Weighted engagement combining reach and interaction depth."""
    views = v["views"] or 0
    likes = v["likes"] or 0
    comments = v["comments"] or 0
    shares = v["shares"] or 0
    # Shares and comments signal stronger intent than passive likes
    return views + (likes * 2) + (comments * 5) + (shares * 8)


def _enrich_video(conn, video: dict) -> dict | None:
    """Return enrichment dict, fetching from DB or calling Claude as needed."""
    if video["enrichment_json"]:
        try:
            return json.loads(video["enrichment_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    song_name = video["song_name"]
    artist = video["song_artist"] or "Unknown"
    if not song_name:
        return None

    try:
        data = enrich_song(song_name, artist)
        conn.execute(
            "UPDATE videos SET enrichment_json=? WHERE id=?",
            (json.dumps(data), video["id"]),
        )
        return data
    except Exception:
        return None


def _distribution(values: list[str]) -> dict[str, float]:
    """Turn a list of categorical values into a probability distribution."""
    if not values:
        return {}
    counts = Counter(values)
    total = len(values)
    return {k: round(v / total, 3) for k, v in counts.most_common()}


def _top_arrangements(all_lists: list[list[str]], top_n: int = 4) -> list[str]:
    flat = [item for sublist in all_lists for item in sublist]
    return [item for item, _ in Counter(flat).most_common(top_n)]


def build_fingerprint() -> dict:
    """
    Build and persist a style fingerprint from the top 20% of videos.
    Returns the fingerprint dict.
    """
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, song_name, song_artist, views, likes, comments, shares,
                      is_cover, enrichment_json
               FROM videos
               ORDER BY views DESC"""
        ).fetchall()

    if not rows:
        return {"error": "no_videos", "message": "Import some videos first."}

    videos = [dict(r) for r in rows]
    total = len(videos)

    # Score and sort by engagement
    for v in videos:
        v["_score"] = _engagement_score(v)
    videos.sort(key=lambda v: v["_score"], reverse=True)

    # Top 20%, minimum 3
    cutoff = max(3, math.ceil(total * 0.20))
    top_videos = videos[:cutoff]

    # Enrich each top video
    enrichments = []
    top_song_refs = []

    with get_db() as conn:
        for v in top_videos:
            e = _enrich_video(conn, v)
            if e:
                enrichments.append(e)
                if v["song_name"]:
                    top_song_refs.append({
                        "song_name": v["song_name"],
                        "song_artist": v["song_artist"],
                        "views": v["views"],
                        "score": round(v["_score"]),
                    })

    if not enrichments:
        return {"error": "no_enrichments", "message": "Could not enrich any top videos."}

    # Aggregate
    def collect(field):
        return [e[field] for e in enrichments if field in e and e[field] is not None]

    def avg(values):
        return round(sum(values) / len(values), 2) if values else None

    fingerprint = {
        "total_videos": total,
        "sample_size": len(enrichments),
        "top_cutoff_pct": 20,
        "genre": _distribution(collect("genre")),
        "subgenre": _distribution(collect("subgenre")),
        "vocal_range": _distribution(collect("vocal_range")),
        "emotional_tone": _distribution(collect("emotional_tone")),
        "tempo_feel": _distribution(collect("tempo_feel")),
        "saturation_risk_tolerance": _distribution(collect("saturation_risk")),
        "avg_chorus_recognizability": avg(collect("chorus_recognizability")),
        "avg_nostalgia_factor": avg(collect("nostalgia_factor")),
        "avg_hook_length_seconds": avg(collect("hook_length_seconds")),
        "preferred_arrangements": _top_arrangements(
            [e["cover_arrangements"] for e in enrichments if "cover_arrangements" in e]
        ),
        "top_songs": top_song_refs[:10],
    }

    # Persist
    with get_db() as conn:
        conn.execute(
            "INSERT INTO style_fingerprint (fingerprint_json) VALUES (?)",
            (json.dumps(fingerprint),),
        )

    return fingerprint


def get_latest_fingerprint() -> dict | None:
    """Return the most recently computed fingerprint, or None."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT fingerprint_json, computed_at FROM style_fingerprint ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    fp = json.loads(row["fingerprint_json"])
    fp["computed_at"] = row["computed_at"]
    return fp
