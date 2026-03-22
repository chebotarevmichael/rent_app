from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Any, Self
from pydantic import BaseModel, PrivateAttr


class Base(ABC, BaseModel):
    # it's DB mock
    _db: ClassVar[dict[type, dict[Any, Base]]] = {}

    # track changed fields
    _changed_fields: set[str] = PrivateAttr(default_factory=set)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Base._db[cls] = {}       # mock-table for each class

    # TODO db_id заменить на pk
    @property
    @abstractmethod
    def db_id(self) -> Any:
        raise NotImplementedError

    @classmethod
    def factory(cls, **kwargs: Any) -> Self:
        return cls(**kwargs)

    def update(self, data: dict) -> Self:
        update = self.model_dump()
        update.update(data)
        for k, v in self.model_validate(update).model_dump(exclude_defaults=True).items():
            old_value = getattr(self, k, None)
            if old_value != v:
                self._changed_fields.add(k)
            setattr(self, k, v)
        return self

    # ==== tracking of changes ====

    def is_changed(self) -> bool:
        return bool(self._changed_fields)

    def model_post_init(self, __context) -> None:  # pydantic v2 hook
        super().model_post_init(__context)
        self._changed_fields.clear()

    # ==== ORM mock ====

    @classmethod
    def _get_table(cls) -> dict[Any, Self]:
        return Base._db[cls]  # type: ignore[return-value]

    @classmethod
    def get(cls, db_id: Any) -> Self | None:
        return cls._get_table().get(db_id)

    @classmethod
    def bulk_get(cls, db_ids: list[str]) -> list[Self]:
        _table = cls._get_table()
        return [_table[db_id] for db_id in db_ids if db_id in _table]

    def save(self, data: dict[str, Any] | None = None) -> Self:
        if data:
            self.update(data)
        _table: dict[Any, Self] = Base._db[type(self)]  # type: ignore[assignment]
        _table[self.db_id] = self
        return self

    @classmethod
    def bulk_save(cls, entities: list[Self]) -> list[Self]:
        _table = cls._get_table()
        for entity in entities:
            _table[entity.db_id] = entity
        return entities

    @classmethod
    def delete(cls, db_id: Any) -> None:
        cls._get_table().pop(db_id, None)

    @classmethod
    def is_exist(cls, db_id: Any) -> bool:
        return db_id in cls._get_table()
