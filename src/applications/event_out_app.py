from datetime import datetime

from src.domains import EventOut
from src.repositories import EventOutRepository, event_repo


class EventOutApp:
    repo: EventOutRepository = event_repo

    def get(self, event_id: str) -> EventOut | None:
        return self.repo.get(db_id=event_id)

    def create(self, data: dict[str]) -> EventOut:
        new_event = EventOut.factory(**data)

        # if self.repo.is_exist(db_id=new_event.event_id):
        #     raise DuplicatedEventOut(detail=data)

        return self.repo.create(new_event)

    def update(self, data: dict[str], event: EventOut | None = None) -> EventOut:
        # we have no attends to update events
        raise NotImplementedError

    def delete(self, event_id: str) -> None:
        return self.repo.delete(db_id=event_id)

    # TODO: add bulk_delete + bulk_create
    def bulk_get_by_ts(self, ts: datetime) -> list[EventOut]:
        return self.repo.bulk_get_by_ts(ts)

    def bulk_create(self, out_event: list[EventOut]) -> list[EventOut]:
        return self.bulk_create(out_event)



event_out_app_impl = EventOutApp()
