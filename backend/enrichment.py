import json
import os
import time
from anthropic import Anthropic, APITimeoutError, APIConnectionError, InternalServerError

client = Anthropic(timeout=120.0)


def _call_with_retry(fn, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except (APITimeoutError, APIConnectionError, InternalServerError) as e:
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

_SYSTEM = """\
You are a music analyst with deep knowledge of popular songs, vocal styles, and creator trends on TikTok and Instagram.
When given a song title and artist, return a JSON object with exactly these fields — no extra text, no markdown, just raw JSON.

Field specs:
- genre: primary genre string (e.g. "pop", "indie pop", "country", "R&B")
- subgenre: more specific style (e.g. "bedroom pop", "folk pop", "neo soul")
- vocal_range: one of "low" | "mid" | "high"
- emotional_tone: one of "sad" | "nostalgic" | "euphoric" | "empowering" | "romantic" | "melancholic" | "playful"
- tempo_feel: one of "slow" | "mid" | "uptempo"
- chorus_recognizability: integer 1–10 (10 = everyone knows it instantly)
- cover_arrangements: array of 2–4 strings from ["acoustic guitar", "piano", "voice only", "ukulele", "loop pedal", "full band", "stripped"]
- hook_length_seconds: integer — estimated ideal clip length in seconds for a short-form cover
- audience_fit: string describing age range and gender skew (e.g. "16–24 female", "18–35 mixed")
- nostalgia_factor: integer 1–10 (10 = deeply nostalgic for its era)
- saturation_risk: one of "low" | "medium" | "high" — how many covers already flood the platform
"""

_PROMPT = "Song: {song_name}\nArtist: {artist}\n\nReturn the JSON enrichment object."


def enrich_song(song_name: str, artist: str) -> dict:
    """Call Claude to enrich a song with structured metadata. Returns a dict."""
    message = _call_with_retry(client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=_SYSTEM,
        messages=[
            {"role": "user", "content": _PROMPT.format(song_name=song_name, artist=artist)}
        ],
    )
    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
