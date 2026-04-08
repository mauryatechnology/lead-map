from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
import re


class ExtractionRequest(BaseModel):
    maps_url: str
    city: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    max_results: Optional[int] = None
    scroll_delay: float = 1.5

    @validator("maps_url")
    def validate_maps_url(cls, v):
        if "google.com/maps" not in v and "maps.google" not in v:
            raise ValueError("Must be a valid Google Maps URL")
        return v


class Lead(BaseModel):
    name: str = ""
    city: str = ""
    instagram: str = ""
    phone: str = ""
    website: str = ""
    notes: str = ""
    about: str = ""
    extracted_at: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ExtractionStatus(BaseModel):
    job_id: str
    status: str  # pending | running | completed | stopped | failed
    total_found: int = 0
    leads: List[Lead] = []
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_message: str = ""
    maps_url: Optional[str] = None


class StopRequest(BaseModel):
    job_id: str
