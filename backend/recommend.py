"""
Recommendation Engine

Scores candidate songs against Summer's style fingerprint,
generates Claude coaching tips, and stores results in the DB.
"""

import json
import time
from anthropic import Anthropic, APITimeoutError, APIConnectionError, InternalServerError
from database import get_db
from enrichment import enrich_song
from fingerprint import get_latest_fingerprint

client = Anthropic(timeout=120.0)


def _call_with_retry(fn, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except (APITimeoutError, APIConnectionError, InternalServerError):
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)


_TIP_SYSTEM = """\
You are a music career coach for Summer Victoria — a singer with 125k TikTok followers known for warm, intimate acoustic covers.
Given a song's musical profile and Summer's proven style, write a 2-3 sentence coaching tip.

The tip must:
- Explain specifically WHY this song is a strong fit for Summer's audience right now
- Suggest one concrete approach: arrangement style, hook moment, or posting angle
- Sound like a knowledgeable friend, not a corporate memo
- Never mention "fingerprint", "enrichment", "data", or "algorithm"

Output ONLY the tip text. No labels, no bullet points, no quotes.
"""

_TIP_PROMPT = """\
Song: {song_name} by {artist}
Genre: {genre} / {subgenre}
Emotional tone: {emotional_tone}
Tempo: {tempo_feel}
Vocal range: {vocal_range}
Chorus recognizability: {chorus_recognizability}/10
Nostalgia factor: {nostalgia_factor}/10
Saturation risk: {saturation_risk}
Best arrangements: {arrangements}

Summer's proven sweet spots:
- Top genres: {top_genres}
- Top tones: {top_tones}
- Preferred tempo: {top_tempo}
- Avg chorus recognizability she does well with: {avg_cr}/10
- Preferred arrangements: {pref_arrangements}
"""


def _score_distribution(value: str | None, dist: dict) -> float:
    if not value or not dist:
        return 0.0
    return dist.get(value, 0.0)


def _score_proximity(value: float | None, target: float | None, max_diff: float = 4.0) -> float:
    if value is None or target is None:
        return 0.0
    return max(0.0, 1.0 - abs(value - target) / max_diff)


def score_against_fingerprint(enrichment: dict, fingerprint: dict) -> float:
    """Return a style_fit_score between 0.0 and 1.0."""
    weights = {
        "genre":       3.0,
        "tone":        2.5,
        "vocal_range": 2.0,
        "tempo":       1.5,
        "chorus_cr":   1.5,
        "nostalgia":   1.0,
        "risk":        1.5,
    }

    scores = {
        "genre":   _score_distribution(enrichment.get("genre"), fingerprint.get("genre", {})),
        "tone":    _score_distribution(enrichment.get("emotional_tone"), fingerprint.get("emotional_tone", {})),
        "vocal_range": _score_distribution(enrichment.get("vocal_range"), fingerprint.get("vocal_range", {})),
        "tempo":   _score_distribution(enrichment.get("tempo_feel"), fingerprint.get("tempo_feel", {})),
        "chorus_cr": _score_proximity(
            enrichment.get("chorus_recognizability"),
            fingerprint.get("avg_chorus_recognizability"),
        ),
        "nostalgia": _score_proximity(
            enrichment.get("nostalgia_factor"),
            fingerprint.get("avg_nostalgia_factor"),
        ),
        "risk": _score_distribution(
            enrichment.get("saturation_risk"),
            fingerprint.get("saturation_risk_tolerance", {}),
        ),
    }

    total_weight = sum(weights.values())
    weighted_sum = sum(scores[k] * weights[k] for k in weights)
    return round(weighted_sum / total_weight, 4)


def _generate_tip(song_name: str, artist: str, enrichment: dict, fingerprint: dict) -> str:
    top_genres = ", ".join(list(fingerprint.get("genre", {}).keys())[:3]) or "mixed"
    top_tones = ", ".join(list(fingerprint.get("emotional_tone", {}).keys())[:3]) or "mixed"
    top_tempo = ", ".join(list(fingerprint.get("tempo_feel", {}).keys())[:2]) or "mixed"
    pref_arr = ", ".join(fingerprint.get("preferred_arrangements", [])[:3]) or "acoustic"

    prompt = _TIP_PROMPT.format(
        song_name=song_name,
        artist=artist,
        genre=enrichment.get("genre", ""),
        subgenre=enrichment.get("subgenre", ""),
        emotional_tone=enrichment.get("emotional_tone", ""),
        tempo_feel=enrichment.get("tempo_feel", ""),
        vocal_range=enrichment.get("vocal_range", ""),
        chorus_recognizability=enrichment.get("chorus_recognizability", "?"),
        nostalgia_factor=enrichment.get("nostalgia_factor", "?"),
        saturation_risk=enrichment.get("saturation_risk", "?"),
        arrangements=", ".join(enrichment.get("cover_arrangements", [])),
        top_genres=top_genres,
        top_tones=top_tones,
        top_tempo=top_tempo,
        avg_cr=fingerprint.get("avg_chorus_recognizability", "?"),
        pref_arrangements=pref_arr,
    )

    response = _call_with_retry(
        client.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=_TIP_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_recommendations(candidates: list[dict], trending_weight: float = 0.3) -> list[dict]:
    """
    Score and tip a list of candidate songs.

    Each candidate: {"song_name": str, "artist": str, "trending_score": float 0-1}
    Returns list of dicts ready to insert into recommendations table.
    """
    fingerprint = get_latest_fingerprint()
    if not fingerprint:
        raise ValueError("No style fingerprint found. Build one first.")

    results = []
    for c in candidates:
        song_name = c["song_name"].strip()
        artist = c.get("artist", "").strip() or "Unknown"
        trending_score = float(c.get("trending_score", 0.5))

        try:
            enrichment = enrich_song(song_name, artist)
        except Exception:
            continue

        style_fit = score_against_fingerprint(enrichment, fingerprint)
        final_score = round(
            (trending_score * trending_weight) + (style_fit * (1 - trending_weight)), 4
        )

        try:
            tip = _generate_tip(song_name, artist, enrichment, fingerprint)
        except Exception:
            tip = None

        results.append({
            "song_name": song_name,
            "song_artist": artist,
            "trending_score": trending_score,
            "style_fit_score": style_fit,
            "final_score": final_score,
            "tip_text": tip,
            "status": "pending",
            "enrichment_json": json.dumps(enrichment),
        })

    results.sort(key=lambda r: r["final_score"], reverse=True)

    with get_db() as conn:
        for r in results:
            conn.execute(
                """INSERT INTO recommendations
                   (song_name, song_artist, trending_score, style_fit_score,
                    final_score, tip_text, status)
                   VALUES (?,?,?,?,?,?,?)""",
                (r["song_name"], r["song_artist"], r["trending_score"],
                 r["style_fit_score"], r["final_score"], r["tip_text"], r["status"]),
            )

    return results
