from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Body
from pydantic import BaseModel, Field, EmailStr, field_validator

from src.api.utils import build_router
from src.models import EventIn, User, EventInType, UserRiskSegment

from src.api.exceptions import DuplicatedEvent
from src.scripts.cron import cron_generate_out_events

router = build_router(__name__)


class RequestUserTraits(BaseModel):
    email: EmailStr
    country: str = 'ZZ'  # country can NULL (empty) or ZZ (unknown)
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
    # create events
    new_event = EventIn.factory(**request.model_dump())

    if EventIn.is_exist(db_id=new_event.event_id):
        raise DuplicatedEvent(event_id=new_event.event_id, user_id=new_event.user_id)

    # user
    user = User.get(db_id=request.user_id)
    if not user:
        # todo NOTE:
        #  Не хочется давать возможность создавать пользователей по ивенту извне,
        #  по идее мы уже должны знать о нашем юзере перед тем как принимать ивенты по пользователю.
        #  .
        #  Но если так сделать, то в текущей системе пользователям совсем неоткуда будет взяться,
        #  поэтому разрешаем создавать пользователей на основе любого входящего ивента((
        # raise UnknownEventUser(user_id=request.user_id)
        user = User.factory(user_id=request.user_id, **request.user_traits.model_dump())
    else:
        user.update(request.user_traits.model_dump())

    # todo NOTE:
    #  Работа с 2 таблицами только через тр-цию, но т.к. БД замокана - делаем без контекстного менеджера
    if user.is_changed:
        user.save()     # create/update the user (only if it's really changed)
    new_event.save()    # save the event

    # todo NOTE:
    #  ЭТО УМЫШЛЕННЫЙ ХАК!!!
    #  Чтобы вы не ждали 1 минуту между самим запросом и тем как буду созданы исходящие события,
    #  которые в том числе станут видны в audit-ручку.
    #  .
    #  Считайте, что этого вызова тут нет, а автор уже жалеет о том, что сделал этот хак))
    cron_generate_out_events(actual_users_ids=[user.user_id])

    return {
        'status': 'accepted',
        'event_id': new_event.event_id,
        'event_type': new_event.event_type,
        'user_id': new_event.user_id,
        'stored': True,
    }
