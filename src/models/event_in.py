from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import Field, field_validator
from typing import Any, Self

from src.models import Base


# todo NOTE: в ТЗ типы событий написаны строчными буквами (а так, конечно, хочется сделать единообразно - капсом)
class EventInType(str, Enum):
    SIGNUP_COMPLETED = 'signup_completed'
    LINK_BANK_SUCCESS = 'link_bank_success'
    PAYMENT_INITIATED = 'payment_initiated'
    PAYMENT_FAILED = 'payment_failed'


class EventInFailureReason(str, Enum):
    INSUFFICIENT_FUNDS = 'INSUFFICIENT_FUNDS'
    OTHER = 'OTHER'


class EventIn(Base):
    event_id: str  # format: '{event_type}:{user_id}:{event_timestamp.isoformat()}'
    event_type: EventInType

    user_id: str
    event_timestamp: datetime
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def db_id(self) -> str:
        return self.event_id

    @field_validator('event_timestamp', mode='before')
    def ensure_utc(cls, v: datetime) -> datetime:
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v

    def __eq__(self, other: object):
        if not isinstance(other, EventIn):
            return NotImplemented
        return self.event_id == other.event_id

    def __lt__(self, other: object):
        if not isinstance(other, EventIn):
            return NotImplemented
        return self.event_timestamp < other.event_timestamp

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

    # todo NOTE:
    #  Если бы мы работали с БД, то могли бы убрать 2 мок-метода ниже.
    #  Мы бы использовали единый метод bulk_get (наследованный от Base) как-то так:
    #      in_events = EventIn.bulk_get(
    #         ('event_timestamp', operator.ge, ts),       # condition #1
    #         ('user_id', operator.eq, request.user_id),  # condition #2
    #         ...
    #         no_pagination=True,
    #      )

    @classmethod
    def bulk_get_by_ts(cls, ts: datetime) -> list[EventIn]:
        return [event for event in cls._get_table().values() if event.event_timestamp >= ts]

    @classmethod
    def bulk_get_by_user_ids(cls, user_ids: list[str]) -> list[Self]:
        _user_ids_set = set(user_ids)
        return [event for event in cls._get_table().values() if event.user_id in _user_ids_set]