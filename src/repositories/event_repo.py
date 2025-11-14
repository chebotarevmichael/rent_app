from datetime import datetime

from src.domains import EventIn
from src.repositories import BaseRepository


# TODO: в реальной жизни будет простой балковый запрос с фильтрами под которые есть индекс BTREE(ts) + BTREE(user_id)
class EventRepository(BaseRepository):
    def bulk_get_by_ts(self, ts: datetime) -> list[EventIn]:
        return [event for event in self._cache.values() if event.event_timestamp >= ts]

    def bulk_get_by_user_ids(self, user_ids: list[str]) -> list[EventIn]:
        _user_ids_set = set(user_ids)
        return [event for event in self._cache.values() if event.user_id in _user_ids_set]


event_repo = EventRepository()
