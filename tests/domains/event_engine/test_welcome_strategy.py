from datetime import datetime, timezone, timedelta

from src.models import EventOut, EventOutType, EventInType, EventOutState
from src.scripts.cron import cron_generate_out_events

from tests.conftest import user, event_in


def test_basic(user, event_in):
    _ = "Базовый тест. 1 входящее и 1 исходящее"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    signup = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now, user=user)

    # call welcome strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])

    assert len(out_events) == 1, 'Only 1 out event'

    out = out_events[0]
    assert out.event_type == EventOutType.WELCOME_EMAIL, 'event type is not WELCOME_EMAIL'
    assert out.user_id == user.user_id, 'user_id'
    assert out.state == EventOutState.READY, 'state is not READY'
    assert out.linked_in_events_ids == [signup.event_id], 'linked_in_events_ids'


def test_3_in_events(user, event_in):
    _ = "3 Одновременно. 3 входящих, 1 успешное и 2 подавленных"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    in_1 = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now, user=user)
    in_2 = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now + timedelta(seconds=1), user=user)
    in_3 = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now + timedelta(seconds=600), user=user)

    # call welcome strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort(key=lambda x: x.event_timestamp)

    assert len(out_events) == 3, '3 out event'
    out_1, out_2, out_3 = out_events

    # first
    assert out_1.event_type == EventOutType.WELCOME_EMAIL, '#1 event type is not WELCOME_EMAIL'
    assert out_1.state == EventOutState.READY, '#1 state'
    assert out_1.linked_in_events_ids == [in_1.event_id], '#1 linked_in_events_ids'

    # second
    assert out_2.event_type == EventOutType.WELCOME_EMAIL, '#2 event type is not WELCOME_EMAIL'
    assert out_2.state == EventOutState.SUPPRESSED, '#2 state'
    assert out_2.linked_in_events_ids == [in_2.event_id], '#2 linked_in_events_ids'

    # third
    assert out_3.event_type == EventOutType.WELCOME_EMAIL, '#3 event type is not WELCOME_EMAIL'
    assert out_3.state == EventOutState.SUPPRESSED, '#3 state'
    assert out_3.linked_in_events_ids == [in_3.event_id], '#3 linked_in_events_ids'


def test_event_from_past(user, event_in):
    _ = "Событие из прошлого."

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()

    in_from_now = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now, user=user)
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # yet another input event, BUT it from past
    in_from_past = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now - timedelta(hours=1), user=user)
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort(key=lambda x: x.event_timestamp)

    assert len(out_events) == 2, '2 out event'
    out_1, out_2 = out_events

    # first
    assert out_1.event_type == EventOutType.WELCOME_EMAIL, '#1 event type is not WELCOME_EMAIL'
    assert out_1.state == EventOutState.READY, '#1 state'
    assert out_1.linked_in_events_ids == [in_from_now.event_id], '#1 linked_in_events_ids'

    # second
    assert out_2.event_type == EventOutType.WELCOME_EMAIL, '#2 event type is not WELCOME_EMAIL'
    assert out_2.state == EventOutState.SUPPRESSED, '#2 state'
    assert out_2.linked_in_events_ids == [in_from_past.event_id], '#2 linked_in_events_ids'
