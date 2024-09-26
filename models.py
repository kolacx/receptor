from datetime import datetime

from pydantic import BaseModel, Field
from typing import Optional


class Destination(BaseModel):
    destinationName: str
    transport: str  # e.g., 'http.post', 'log.info'
    url: Optional[str] = None  # For http-based transports


class Strategy(BaseModel):
    name: str
    python_code: Optional[str] = None  # For custom strategy code


class Logs(BaseModel):
    request: Optional[dict] = None
    response: Optional[dict] = None

    destination: str
    transport: str
    url: Optional[str] = None
    strategy: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.now)
