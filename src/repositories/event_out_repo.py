from datetime import datetime

from src.domains import EventOut
from src.repositories import BaseRepository


class EventOutRepository(BaseRepository):
    def bulk_get_by_ts(self, ts: datetime) -> list[EventOut]:
        # TODO: в реальной жизни это будет простой балковый запрос с фильтрами под которые есть индекс BTREE
        return [event for event in self._cache.values() if event.event_timestamp >= ts]

event_out_repo = EventOutRepository()
