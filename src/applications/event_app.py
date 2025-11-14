from datetime import datetime

from src.domains import EventIn
from src.exceptions import DuplicatedEvent
from src.repositories import EventRepository, event_repo


class EventApp:
    repo: EventRepository = event_repo

    def get(self, event_id: str) -> EventIn | None:
        return self.repo.get(db_id=event_id)

    def bulk_get_by_user_ids(self, user_ids: list[str]) -> list[EventIn]:
        # TODO: да, мы выгребаем все события пользователя, НО в реальной жизни у нас будет мы будем вытаскивать
        #  "последние N событий с distinct по типу", т.е. последние события по 1шт каждого типа (в зависимости
        #  от самой "злой" стратегии нужно будет тянуть больше или меньше событий, нужно больше конкретике о системе)
        #  .
        #  Пока для простоты тянем все что есть для конкретных пользователей.
        return self.repo.bulk_get_by_user_ids(user_ids=user_ids)

    def create(self, data: dict[str]) -> EventIn:
        new_event = EventIn.factory(**data)

        if self.repo.is_exist(db_id=new_event.event_id):
            raise DuplicatedEvent(detail=data)

        return self.repo.create(new_event)

    def update(self, data: dict[str], event: EventIn | None = None) -> EventIn:
        # we have no attends to update events
        raise NotImplementedError

    def delete(self, event_id: str) -> None:
        return self.repo.delete(db_id=event_id)

    def bulk_get_by_ts(self, ts: datetime) -> list[EventIn]:
        return self.repo.bulk_get_by_ts(ts)


event_app_impl = EventApp()
