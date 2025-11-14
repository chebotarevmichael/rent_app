from __future__ import annotations

from abc import ABC
from datetime import datetime
from typing import TypeVar

T = TypeVar('T')


class BaseRepository(ABC):
    # singletons
    _instances: dict[type, BaseRepository] = {}

    # create child singleton
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
        return cls._instances[cls]

    # init the child singleton only at once
    def __init__(self):
        if not hasattr(self, "_cache"):
            self._cache: dict[str, T] = {}

    def get(self, db_id: str | tuple) -> T | None:
        return self._cache.get(db_id, None)

    def bulk_get(self, db_ids: list[str]) -> list[T]:
        return [self._cache[db_id] for db_id in db_ids if db_id in self._cache]

    def is_exist(self, db_id: str | tuple) -> bool:
        return db_id in self._cache

    def create(self, entity: T) -> T:
        self._cache[entity.db_id] = entity
        return entity

    def bulk_create(self, entities: list[T]) -> list[T]:
        for entity in entities:
            self._cache[entity.db_id] = entity
        return entities

    def update(self, entity: T) -> T:
        self._cache[entity.db_id] = entity
        return entity

    def delete(self, db_id: str | tuple) -> None:
        self._cache.pop(db_id, None)
