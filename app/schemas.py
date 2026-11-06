from pydantic import BaseModel, HttpUrl
from typing import List, Dict

class TravelAnalyzeRequest(BaseModel):
    google_maps_url: HttpUrl

class AspectScore(BaseModel):
    negatif: float
    netral: float
    positif: float
    prediksi_tertinggi: str

class TravelAnalyzeResponse(BaseModel):
    travel_name: str
    total_reviews_analyzed: int
    sentiment_analysis_summary: Dict[str, AspectScore]
    raw_reviews: List[str]