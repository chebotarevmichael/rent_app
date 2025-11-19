from __future__ import annotations

from datetime import datetime, timezone, timedelta

from src.models import EventIn, User, EventOut
from src.domains.event_engine import event_strategies

from src.tools import group_list_by_key, group_set_by_key


# TODO: добавить автозапуск
def cron_generate_out_events(
        # for manual execution in production
        event_timestamp: datetime = None,
        # for tests
        actual_users_ids: list[str] = None,
        _now: datetime = None,
):
    # TODO:
    #  С учетом ввводных "Пользователей 100к и будет 1кк через год" и "РПС по ивентам 5-20", крон скрипт будет
    #  выгребать от 5*60=300 и да 20*60=1200 событий вначале при 100к пользователей;
    #  Даже при 1кк юзеров в будущем, будет от 3.000 до 12.000 событий в минуту.
    #  Для такого крон-скрипта будет оставаться запас. Дешево и сердито, в последующем может быть легко превращено в
    #  отдельные воркеры, которые запускаются под каждого пользователя (но тогда возврастет кол-во запросов на БД)
    #  .
    #  Плюсы: 1 запрос на ивенты, 1 запрос на юзеров, легко реализуется вначале и имеет запас к масштабированию
    #  Минусы: так или иначе мы все равно упремся в предел вертикального масштабирования, но там скорее проще
    #          крон скрипт разделить на 2шт по куче типов событий для каждого.

    # parameter for test and executing in production
    if actual_users_ids is None:
        event_timestamp = event_timestamp or (datetime.now(timezone.utc) - timedelta(minutes=30))
        last_30_min_events_in = EventIn.bulk_get_by_ts(ts=event_timestamp)
        actual_users_ids = list({event.user_id for event in last_30_min_events_in})

    # input events
    actual_users_events_in = EventIn.bulk_get_by_user_ids(user_ids=actual_users_ids)
    user_id2events_in: dict[str, list[EventIn]] = group_list_by_key(items=actual_users_events_in, key='user_id')

    # output events
    actual_users_out_events = EventOut.bulk_get_by_user_ids(user_ids=actual_users_ids)
    user_id2out_events = group_set_by_key(items=actual_users_out_events, key='user_id')

    # users
    users = User.bulk_get(db_ids=actual_users_ids)

    for user in users:
        user_in_events: list[EventIn] = user_id2events_in.get(user.user_id, [])
        user_in_events.sort()
        user_out_events: set[EventOut] = user_id2out_events.get(user.user_id, set())

        # create new out events for user
        created_out_events = set()
        for strategy in event_strategies:
            created_out_events |= strategy.extend_out_events(
                in_events=user_in_events,
                out_events=user_out_events,
                user=user,
                _now=_now,
            )

        # push or suppress created event
        for strategy in event_strategies:
            strategy.judge_out_events(in_events=user_in_events, out_events=user_out_events, _now=_now)

        # write new out events for current user to DB
        EventOut.bulk_save(entities=created_out_events)

        # TODO: тут нужно поставить джобу в очередь при этом в одном тра-ции с созданием ивента в БД
