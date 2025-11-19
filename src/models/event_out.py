from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Self, TYPE_CHECKING

from src.models import Base
from src.tools import int_hash, gen_id

if TYPE_CHECKING:
    from src.models import EventIn, User


logger = logging.getLogger(__name__)


class EventOutType(str, Enum):
    WELCOME_EMAIL = 'WELCOME_EMAIL'
    BANK_LINK_NUDGE_SMS = 'BANK_LINK_NUDGE_SMS'
    INSUFFICIENT_FUNDS_EMAIL = 'INSUFFICIENT_FUNDS_EMAIL'
    HIGH_RISK_ALERT = 'HIGH_RISK_ALERT'


# todo NOTE:
#  В реальной жизни статуса CREATED не было бы, в SQL-таблице на поле было бы "state IS NOT NULL",
#  а у энтити поле state при создании был бы None.
#  но т.к. в текущем коде схема БД опущена, сделал статус в явном виде.
class EventOutState(str, Enum):
    CREATED = 'CREATED'         # only in memory, this state can not be in DB

    READY = 'READY'             # processing
    PROCESSING = 'PROCESSING'

    DONE = 'DONE'               # finished
    SUPPRESSED = 'SUPPRESSED'


class EventOutChannel(str, Enum):
    SMS = 'SMS'
    EMAIL = 'EMAIL'
    INTERNAL_ALERT = 'INTERNAL_ALERT'


class EventOut(Base):
    event_id: str

    # fields for hash
    event_type: EventOutType
    user_id: str
    linked_in_events_ids: list[str]

    state: EventOutState
    channel: EventOutChannel
    event_timestamp: datetime
    message: str
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

    def __eq__(self, other: object):
        if not isinstance(other, EventOut):
            return NotImplemented
        return (
            self.event_type == other.event_type and
            self.user_id == other.user_id and
            self.linked_in_events_ids == other.linked_in_events_ids
        )

    def __lt__(self, other: object):
        if not isinstance(other, EventOut):
            return NotImplemented
        return self.event_timestamp < other.event_timestamp


    # TODO: какое действие должно быть? послать в канал или еще что
    #  только скорее должно быть перенесено в апку
    def execute(self):
        logger.info(
            '%s. %s. user_id=%s, channel=%s, event_type=%s, linked_in_events_ids=%s, explanation=%s',
            self.event_timestamp,
            self.message,
            self.user_id,
            self.channel,
            self.explanation,
        )
        self.state = EventOutState.DONE


    @classmethod
    def factory(cls, linked_in_events: list[EventIn], user: User, **kwargs) -> Self:
        # todo NOTE:
        #  Потенциально кроме linked_IN_events могут добавиться linked_OUT_events
        #  (например: "если уже послали 2 письма и нет эффекта, значит в следующий раз посылаем смс")
        linked_in_events.sort()

        return cls(
            event_id=gen_id(),
            state=EventOutState.CREATED,
            user_id=user.user_id,
            event_timestamp=kwargs.pop('_now', None) or datetime.now(timezone.utc),
            linked_in_events_ids=[in_event.event_id for in_event in linked_in_events],
            **kwargs,
        )

    # === ORM methods ===

    # todo NOTE::
    #  Осознанный копипаст с класса EventIn, чтобы не плодить Mixin'ы с единственным 2-строчным методом

    @classmethod
    def bulk_get_by_user_ids(cls, user_ids: list[str]) -> list[Self]:
        _user_ids_set = set(user_ids)
        return [event for event in cls._get_table().values() if event.user_id in _user_ids_set]