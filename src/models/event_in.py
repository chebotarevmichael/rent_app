from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import Field, field_validator
from typing import Any, Self

from src.models import Base


class EventInType(str, Enum):
    SIGNUP_COMPLETED = 'SIGNUP_COMPLETED'
    LINK_BANK_SUCCESS = 'LINK_BANK_SUCCESS'
    PAYMENT_INITIATED = 'PAYMENT_INITIATED'
    PAYMENT_FAILED = 'PAYMENT_FAILED'


# TODO: when we will have new events with another format, we will create abstract class Event and families of events
#  (each system usually has unified format of all events,
#  therefore we can make one sub-class with several event types for each of service)
class EventIn(Base):
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

    @classmethod
    def factory(cls, event_type: EventInType, user_id: str, event_timestamp: datetime, **kwargs) -> Self:
        return cls(
            event_id=f'{event_type}:{user_id}:{event_timestamp.isoformat()}',
            event_type=event_type,
            user_id=user_id,
            event_timestamp=event_timestamp,
            **kwargs,
        )

    # === ORM methods ===

    # TODO: ATTENTION!!! If we work with DB we can remove this mock-methods, and use some call like this:
    #  in_events = EventIn.bulk_get(
    #     ('event_timestamp', operator.ge, ts),       # condition #1
    #     ('user_id', operator.eq, request.user_id),  # condition #2
    #     ...
    #     no_pagination=True,
    #  )

    @classmethod
    def bulk_get_by_ts(cls, ts: datetime) -> list[EventIn]:
        return [event for event in cls._get_table().values() if event.event_timestamp >= ts]

    @classmethod
    def bulk_get_by_user_ids(cls, user_ids: list[str]) -> list[EventIn]:
        _user_ids_set = set(user_ids)
        return [event for event in cls._get_table().values() if event.user_id in _user_ids_set]