from datetime import datetime, timezone

from pydantic import Field, field_validator
from typing import Any

from src.domains import BaseEntity
from src.enums import EventInType


# TODO: when we will have new events with another format, we will create abstract class Event and families of events
#  (each system usually has unified format of all events,
#  therefore we can make one sub-class with several event types for each of service)
class EventIn(BaseEntity):
    event_id: str
    event_type: EventInType

    user_id: str
    event_timestamp: datetime
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def db_id(self) -> str:
        return self.event_id

    @field_validator("event_timestamp", mode="before")
    def ensure_utc(cls, v: datetime) -> datetime:
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v
