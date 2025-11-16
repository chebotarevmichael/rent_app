from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Self, TYPE_CHECKING

from src.models import Base
from src.tools import int_hash, gen_id

if TYPE_CHECKING:
    from src.models import EventIn, User


class EventOutType(str, Enum):
    WELCOME_EMAIL = 'WELCOME_EMAIL'
    BANK_LINK_NUDGE_SMS = 'BANK_LINK_NUDGE_SMS'
    INSUFFICIENT_FUNDS_EMAIL = 'INSUFFICIENT_FUNDS_EMAIL'
    HIGH_RISK_ALERT = 'HIGH_RISK_ALERT'


class EventOutState(str, Enum):
    # only in memory, this state can not be in DB
    # TODO: в реальной жизни этого статуса бы не было, в таблице state IS NOT NULL, а у энтити state при создании был бы None.
    #  но т.к. в текущем коде не схемы БД, сделал статус в явном виде, иначе было бы не понятно.
    CREATED = 'CREATED'

    # processing
    READY = 'READY'
    PROCESSING = 'PROCESSING'

    # finished
    DONE = 'DONE'
    SUPPRESSED = 'SUPPRESSED'


class EventOut(Base):
    event_id: str

    # fields for hash
    event_type: EventOutType
    user_id: str
    linked_in_events: list[str]

    state: EventOutState
    event_timestamp: datetime
    explanation: str | None = None

    @property
    def db_id(self) -> str:
        return self.event_id

    @property
    def is_in_pipeline(self) -> bool:
        # If true, that means we already have an out event, which will be processed asap, or it was finished.
        return self.state in {EventOutState.READY, EventOutState.PROCESSING, EventOutState.DONE}

    def __hash__(self) -> int:
        return int_hash(self.event_type, self.user_id, *self.linked_in_events_ids, )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EventOut):
            return False
        return (
            self.event_type == other.event_type and
            self.user_id == other.user_id and
            self.linked_in_events_ids == other.linked_in_events_ids
        )

    # TODO: какое действие должно быть? послать в канал или еще что
    #  только скорее должно быть перенесено в апку
    def execute(self):
        pass
        self.state = EventOutState.DONE

    @classmethod
    def factory(cls, linked_in_events: list[EventIn], user: User, **kwargs) -> Self:
        # TODO: потенциально могут быть linked_out_events (например: "если уже посылали письмо, значит теперь посылаем смс")

        return cls(
            event_id=gen_id(),
            state=EventOutState.CREATED,
            user_id=user.user_id,
            event_timestamp=datetime.now(timezone.utc),
            linked_in_events_ids=sorted(in_event.event_id for in_event in linked_in_events),
            **kwargs,
        )

    # === ORM methods ===

    # TODO: it was copied from EventIn. I don't want to create to many class (even Mixins) because it will make code
    #  less readable

    @classmethod
    def bulk_get_by_user_ids(cls, user_ids: list[str]) -> list[EventIn]:
        _user_ids_set = set(user_ids)
        return [event for event in cls._get_table().values() if event.user_id in _user_ids_set]