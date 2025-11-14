from abc import ABC, abstractmethod
from datetime import datetime
from typing import Self

from pydantic import BaseModel

from src.enums import EventInType


class BaseEntity(ABC, BaseModel):
    @property
    @abstractmethod
    def db_id(self):
        raise NotImplementedError

    @classmethod
    def factory(cls, event_type: EventInType, user_id: str, event_timestamp: datetime, **kwargs) -> Self:
        return cls(
            event_id=f'{event_type}:{user_id}:{event_timestamp.isoformat()}',
            event_type=event_type,
            user_id=user_id,
            event_timestamp=event_timestamp,
            **kwargs,
        )