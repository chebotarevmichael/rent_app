from datetime import datetime, timezone, timedelta

import pytest

from src.models import EventOut, EventOutType, EventInType, EventOutState
from src.scripts.cron import cron_generate_out_events

from tests.conftest import user, event_in


@pytest.mark.parametrize('delay_between_events_sec', [-3600, 0, 24*3600])
def test_race_input_events_lte_24h(user, event_in, delay_between_events_sec):
    _ = "Гонка. События signup и bank_success в разных порядках и всегда 1 исходящее событие BANK_LINK_NUDGE_SMS"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    signup = event_in(
        event_type=EventInType.SIGNUP_COMPLETED,
        event_timestamp=_now - timedelta(seconds=delay_between_events_sec),
        user=user,
    )
    bank_success = event_in(event_type=EventInType.LINK_BANK_SUCCESS, event_timestamp=_now, user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort(key=lambda x: x.event_timestamp)

    assert len(out_events) == 2, '2 out events: welcome + nudge sms'
    out_welcome, out_nudge = out_events

    # out_welcome
    assert out_welcome.event_type == EventOutType.WELCOME_EMAIL, '#1 event type is not WELCOME_EMAIL'
    assert out_welcome.user_id == user.user_id, '#1 user_id'
    assert out_welcome.state == EventOutState.READY, '#1 state is not READY'
    assert out_welcome.linked_in_events_ids == [signup.event_id], '#1 linked_in_events_ids'

    # out_nudge
    assert out_nudge.event_type == EventOutType.BANK_LINK_NUDGE_SMS, '#2 event type is not BANK_LINK_NUDGE_SMS'
    assert out_nudge.user_id == user.user_id, '#2 user_id'
    assert out_nudge.state == EventOutState.READY, '#2 state is not READY'
    _expected = sorted([signup, bank_success], key=lambda x: x.event_timestamp)
    assert out_nudge.linked_in_events_ids == [e.event_id for e in _expected], 'Out event linked with both!'

@pytest.mark.parametrize('delay_between_events_sec', [-24*3600-1, 24*3600+1])
def test_race_input_events_gt_24h(user, event_in, delay_between_events_sec):
    _ = "Гонка. События signup и bank_success в разных порядках, но всегда слишком большая разница"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    signup = event_in(
        event_type=EventInType.SIGNUP_COMPLETED,
        event_timestamp=_now - timedelta(seconds=delay_between_events_sec),
        user=user,
    )
    bank_success = event_in(event_type=EventInType.LINK_BANK_SUCCESS, event_timestamp=_now, user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])

    assert len(out_events) == 1, 'welcome, no nudge sms'
    out_welcome = out_events[0]

    # out_welcome
    assert out_welcome.event_type == EventOutType.WELCOME_EMAIL, '#1 event type is not WELCOME_EMAIL'
    assert out_welcome.state == EventOutState.READY, '#1 state is not READY'
    assert out_welcome.linked_in_events_ids == [signup.event_id], '#1 linked_in_events_ids'


def test_double_bank_success(user, event_in):
    _ = "2 bank_success события. 1 успешное и 1 подавленное"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    signup = event_in(event_type=EventInType.SIGNUP_COMPLETED, event_timestamp=_now - timedelta(hours=10), user=user)
    bank_success_1 = event_in(event_type=EventInType.LINK_BANK_SUCCESS, event_timestamp=_now, user=user)
    bank_success_2 = event_in(event_type=EventInType.LINK_BANK_SUCCESS, event_timestamp=_now + timedelta(seconds=1), user=user)

    # call welcome strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort(key=lambda x: x.event_timestamp)

    assert len(out_events) == 1 + 2, '3 out events'
    out_welcome, out_nudge_1, out_nudge_2 = out_events

    # out_welcome
    assert out_welcome.event_type == EventOutType.WELCOME_EMAIL, 'event type is not WELCOME_EMAIL'

    # out_nudge #1 (READY)
    assert out_nudge_1.event_type == EventOutType.BANK_LINK_NUDGE_SMS, '#1 event type is not BANK_LINK_NUDGE_SMS'
    assert out_nudge_1.user_id == user.user_id, '#1 user_id'
    assert out_nudge_1.state == EventOutState.READY, '#1 state is not READY'
    assert out_nudge_1.linked_in_events_ids == [signup.event_id, bank_success_1.event_id], '#1 Out event linked with both!'

    # out_nudge #1 (SUPPRESSED)
    assert out_nudge_2.event_type == EventOutType.BANK_LINK_NUDGE_SMS, '#2 event type is not BANK_LINK_NUDGE_SMS'
    assert out_nudge_2.user_id == user.user_id, '#2 user_id'
    assert out_nudge_2.state == EventOutState.SUPPRESSED, '#2 state is not SUPPRESSED'
    assert out_nudge_2.linked_in_events_ids == [signup.event_id, bank_success_2.event_id], '#1 Out event linked with both!'


def test_doubled_welcome(user, event_in):
    _ = (
        "Повторное событие welcome не порождает пуш. "
        "События signup х2 и bank_success и х2 исходящих события BANK_LINK_NUDGE_SMS"
    )

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    signup_1 = event_in(
        event_type=EventInType.SIGNUP_COMPLETED,
        event_timestamp=_now - timedelta(hours=1),
        user=user,
    )
    bank_success = event_in(event_type=EventInType.LINK_BANK_SUCCESS, event_timestamp=_now + timedelta(hours=2), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # yet another welcome event
    signup_2 = event_in(
        event_type=EventInType.SIGNUP_COMPLETED,
        event_timestamp=_now + timedelta(hours=1),
        user=user,
    )
    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort(key=lambda x: x.event_timestamp)

    assert len(out_events) == 2 + 2, '4 out events: welcome x2 + nudge x2'
    out_welcome_1, out_nudge_1, out_welcome_2, out_nudge_2 = out_events

    # out_welcome_1
    assert out_welcome_1.event_type == EventOutType.WELCOME_EMAIL, '#1 event type is not WELCOME_EMAIL'
    assert out_welcome_1.state == EventOutState.READY, '#1 state is not READY'

    # out_nudge_1
    assert out_nudge_1.event_type == EventOutType.BANK_LINK_NUDGE_SMS, '#2 event type is not BANK_LINK_NUDGE_SMS'
    assert out_nudge_1.state == EventOutState.READY, '#2 state is not READY'
    assert out_nudge_1.linked_in_events_ids == [signup_1.event_id, bank_success.event_id], '#2 Out event linked with both!'

    # out_welcome_2 (suppressed)
    assert out_welcome_2.event_type == EventOutType.WELCOME_EMAIL, '#3 event type is not WELCOME_EMAIL'
    assert out_welcome_2.state == EventOutState.SUPPRESSED, '#3 state is not READY'

    # out_nudge_2  (suppressed)
    assert out_nudge_2.event_type == EventOutType.BANK_LINK_NUDGE_SMS, '#4 event type is not BANK_LINK_NUDGE_SMS'
    assert out_nudge_2.state == EventOutState.SUPPRESSED, '#4 state is not READY'
    assert out_nudge_2.linked_in_events_ids == [signup_2.event_id, bank_success.event_id], '#4 Out event linked with both!'
