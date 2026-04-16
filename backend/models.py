from pydantic import BaseModel
from typing import Optional


class VideoCreate(BaseModel):
    platform: str
    platform_video_id: str
    title: Optional[str] = None
    caption: Optional[str] = None
    duration_seconds: Optional[int] = None
    posted_at: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    follower_gain: Optional[int] = None
    song_name: Optional[str] = None
    song_artist: Optional[str] = None
    is_cover: int = 0
    is_original: int = 0
    enrichment_json: Optional[str] = None


class VideoResponse(VideoCreate):
    id: int
    created_at: str


class RecommendationCreate(BaseModel):
    song_name: str
    song_artist: Optional[str] = None
    trending_score: float = 0.0
    style_fit_score: float = 0.0
    final_score: float = 0.0
    tip_text: Optional[str] = None
    status: str = "pending"


class RecommendationResponse(RecommendationCreate):
    id: int
    generated_at: str


class RecommendationUpdate(BaseModel):
    status: str


class SettingUpsert(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    key: str
    value: str
