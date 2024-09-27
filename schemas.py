from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class RoutingIntent(BaseModel):
    destinationName: str
    model_config = ConfigDict(extra="allow")


class Event(BaseModel):
    payload: Dict
    routingIntents: List[RoutingIntent]
    strategy: Optional[str] = None


class CreateUser(BaseModel):
    username: str
    password: str


class LoginUser(CreateUser):
    pass