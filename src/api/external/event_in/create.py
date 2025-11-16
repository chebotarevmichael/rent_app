# api.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from fastapi import Body
from pydantic import BaseModel, Field, EmailStr, field_validator

from src.api.utils import build_router
from src.models import EventIn, User, EventOut, EventInType, UserRiskSegment
from src.domains.event_engine import event_strategies

from src.exceptions import UnknownEventUser, DuplicatedEvent
from src.tools import group_list_by_key, group_set_by_key


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
    # TODO: проверить все туду и двойные кавычки (лучше май-пай настроить)

    # нельзя создавать пользователя по ивенту
    user = User.get(db_id=request.user_id)
    if not user:
        raise UnknownEventUser(user_id=request.user_id)

    # TODO: работа с 2 таблицами только через тр-цию

    # создаем событие
    new_event = EventIn.factory(**request.model_dump())
    if EventIn.is_exist(db_id=new_event.event_id):
        raise DuplicatedEvent(event_id=new_event.event_id, user_id=new_event.user_id)

    new_event.save()

    # обновляем данные пользователя
    user.save(data=request.model_dump())

    # TODO: аля вызов задачи на воркера

    return {
        'status': 'accepted',
        'event_id': new_event.event_id,
        'event_type': new_event.event_type,
        'user_id': new_event.user_id,
        'stored': True,
    }


# TODO: запуск раз минуту
def cron_job_for_input_event(event_timestamp: datetime = None):
    # Если во время инцидента наш крон-скрипт упадет, мы сможем его перезапустить в ручном режиме, чтобы нагнать
    # потеряшек; так же наличие параметра упрощает написание тестов.
    # С учетом ввводных "Пользователей 100к и будет 1кк через год" и "РПС по ивентам 5-20", крон скрипт будет
    # выгребать от 5*60=300 и да 20*60=1200 событий вначале при 100к пользователей;
    # Даже при 1кк юзеров в будущем, будет от 3000 до 12000 событий в минуту.
    # Для такого крон-скрипта будет оставаться запас. Дешево и сердито, в последующем может быть легко превращено в
    # отдельные воркеры, которые запускаются под каждого пользователя.
    # .
    # Плюсы: 1 запрос на ивенты, 1 запрос на юзеров, легко реализуется вначале и имеет запас
    # Минусы: если железо дешевое - их нет)) Но так или иначе мы все равно упремся в предел вертикального масштабирования.
    event_timestamp = event_timestamp or (datetime.now(timezone.utc) - timedelta(minutes=30))
    last_30_min_events_in = EventIn.bulk_get_by_ts(ts=event_timestamp)
    actual_users_ids = list({event.user_id for event in last_30_min_events_in})

    # input events
    actual_users_events_in = EventIn.bulk_get_by_user_ids(user_ids=actual_users_ids)
    user_id2events_in = group_list_by_key(items=actual_users_events_in, key='user_id')

    # output events
    actual_users_events_out = EventOut.bulk_get_by_user_ids(user_ids=actual_users_ids)
    user_id2events_out = group_set_by_key(items=actual_users_events_out, key='user_id')

    # users
    users = User.bulk_get(db_ids=actual_users_ids)

    for user in users:
        user_events_in = user_id2events_in.get(user.user_id, [])
        user_events_out = user_id2events_out.get(user.user_id, set())

        # create new out events for user
        created_out_events = set()
        for strategy in event_strategies:
            created_out_events |= strategy.extend_out_event(
                in_events=user_events_in,
                out_events=user_events_out,
                user=user,
            )

        # push or suppress created event
        for strategy in event_strategies:
            strategy.judge_out_event(in_events=user_events_in, out_events=user_events_out)

        # write new out events for current user to DB
        EventOut.bulk_save(entities=created_out_events)































