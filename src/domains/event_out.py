from datetime import datetime
from typing import Self, TYPE_CHECKING

from src.domains import BaseEntity
from src.enums import EventOutState, EventOutType
from src.tools import int_hash, gen_id

if TYPE_CHECKING:
    from src.domains import User, EventIn


class EventOut(BaseEntity):
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
            event_timestamp=datetime.now(),
            linked_in_events_ids=sorted(in_event.event_id for in_event in linked_in_events),
            **kwargs,
        )
