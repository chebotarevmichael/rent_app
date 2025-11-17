from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Body
from pydantic import BaseModel, Field, EmailStr, field_validator

from src.api.utils import build_router
from src.models import EventIn, User, EventInType, UserRiskSegment

from src.api.exceptions import DuplicatedEvent


router = build_router(__name__)


class RequestUserTraits(BaseModel):
    email: EmailStr
    country: str = 'ZZ'  # TODO: i already had deal with it: country can NULL (empty) or ZZ (unknown)
    marketing_opt_in: bool
    risk_segment: UserRiskSegment


class RequestEvent(BaseModel):
    user_id: str = Field(..., min_length=1)
    event_type: EventInType
    event_timestamp: datetime
    properties: dict[str, Any] = Field(default_factory=dict)
    user_traits: RequestUserTraits | None = None

    @field_validator('event_timestamp', mode='before')
    def ensure_utc(cls, v: datetime) -> datetime:
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        return v


@router.post('/create', summary='Ingest an event', tags=['events'])
def create(request: RequestEvent = Body(...)):
    # создаем событие
    new_event = EventIn.factory(**request.model_dump())
    if EventIn.is_exist(db_id=new_event.event_id):
        raise DuplicatedEvent(event_id=new_event.event_id, user_id=new_event.user_id)

    # пользователь
    user = User.get(db_id=request.user_id)
    if not user:
        # TODO: не хочется давать возможность создавать пользователей по ивенту извне,
        #  по идее мы уже должны знать о нашем юзере перед тем как принимать ивенты по пользователю.
        #  .
        #  Но если так сделать, то в текущей системе пользователям неоткуда будет взяться,
        #  поэтому разрешаем создавать пользователей на основе любого входящего ивента((
        # raise UnknownEventUser(user_id=request.user_id)
        user = User.factory(user_id=request.user_id, **request.user_traits.model_dump())
    else:
        user.model_update(update=request.user_traits.model_dump())

    # TODO: работа с 2 таблицами только через тр-цию, но т.к. БД замокана - делаем без контекстного менеджера
    new_event.save()    # сохраняем событие
    user.save()         # обновляем/создаем пользователя

    return {
        'status': 'accepted',
        'event_id': new_event.event_id,
        'event_type': new_event.event_type,
        'user_id': new_event.user_id,
        'stored': True,
    }
