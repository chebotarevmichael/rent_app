from datetime import datetime, timezone, timedelta

import pytest

from src.models import EventOut, EventOutType, EventInType, EventOutState, EventInFailureReason
from src.scripts.cron import cron_generate_out_events

from tests.conftest import user, event_in


@pytest.fixture
def payment_failed_event_in(event_in, user):
    def _create(
        user_id: str = None,
        event_timestamp: datetime = None,
        failure_reason: EventInFailureReason = EventInFailureReason.INSUFFICIENT_FUNDS,
        **overrides,
    ):
        data = {
            'event_type': EventInType.PAYMENT_FAILED,
            'event_timestamp': event_timestamp,
            'user_id': user_id,
            'properties': {
                'failure_reason': failure_reason,
            },
        }

        data.update(overrides)
        return event_in(**data)

    return _create


def test_basic(user, payment_failed_event_in):
    _ = "Базовый тест. Провал оплаты с нужной причиной и создается исходящее событие"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    payment_failed = payment_failed_event_in(event_timestamp=_now, user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 1, 'output event х1'

    insufficient_funds, *_ = out_events
    assert insufficient_funds.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL, 'event type is not INSUFFICIENT_FUNDS_EMAIL'
    assert insufficient_funds.user_id == user.user_id, 'user_id'
    assert insufficient_funds.state == EventOutState.READY, 'state is not READY'
    assert insufficient_funds.linked_in_events_ids == [payment_failed.event_id], 'linked_in_events_ids'


def test_wrong_reason(user, payment_failed_event_in):
    _ = "Провал оплаты, НО причина не та, и исходящего события нет"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    payment_failed_event_in(
        event_timestamp=_now,
        user=user,
        failure_reason=EventInFailureReason.OTHER,
    )

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 0, '0 out events'


def test_double_per_day(user, payment_failed_event_in):
    _ = "Провал оплаты с нужной причиной x2 в 1 день, но создается только 1 исходящее событие"

    _now = datetime.now(tz=timezone.utc)

    # build input data
    user = user()
    payment_failed_1 = payment_failed_event_in(event_timestamp=_now - timedelta(seconds=120), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id], _now=_now - timedelta(seconds=100))
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 1, 'output event х1'

    # add another event
    payment_failed_2 = payment_failed_event_in(event_timestamp=_now - timedelta(seconds=60), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id], _now=_now - timedelta(seconds=50))

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort()
    assert len(out_events) == 2, 'output event х2'

    insufficient_funds_1, insufficient_funds_2 = out_events
    assert insufficient_funds_1.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL, '#1 event type is not INSUFFICIENT_FUNDS_EMAIL'
    assert insufficient_funds_1.user_id == user.user_id, '#1 user_id'
    assert insufficient_funds_1.state == EventOutState.READY, '#1 state is not READY'
    assert insufficient_funds_1.linked_in_events_ids == [payment_failed_1.event_id], '#1 linked_in_events_ids'

    assert insufficient_funds_2.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL, '#2 event type is not INSUFFICIENT_FUNDS_EMAIL'
    assert insufficient_funds_2.user_id == user.user_id, '#2 user_id'
    assert insufficient_funds_2.state == EventOutState.SUPPRESSED, '#2 state is not SUPPRESSED'
    assert insufficient_funds_2.linked_in_events_ids == [payment_failed_2.event_id], '#2 linked_in_events_ids'


def test_double_per_2_days(user, payment_failed_event_in):
    _ = "Провал оплаты с нужной причиной x2 за 2 дня, и создается 2 исходящих события"

    _midnight = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=1, microsecond=0)

    # build input data
    user = user()
    payment_failed_1 = payment_failed_event_in(event_timestamp=_midnight - timedelta(seconds=120), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id], _now=_midnight - timedelta(seconds=60))
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 1, 'output event х1'

    # add another event
    payment_failed_2 = payment_failed_event_in(event_timestamp=_midnight + timedelta(seconds=10), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id], _now=_midnight + timedelta(seconds=20))

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort()
    assert len(out_events) == 2, 'output event х2'

    insufficient_funds_1, insufficient_funds_2 = out_events
    assert insufficient_funds_1.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL, '#1 event type is not INSUFFICIENT_FUNDS_EMAIL'
    assert insufficient_funds_1.user_id == user.user_id, '#1 user_id'
    assert insufficient_funds_1.state == EventOutState.READY, '#1 state is not READY'
    assert insufficient_funds_1.linked_in_events_ids == [payment_failed_1.event_id], '#1 linked_in_events_ids'

    assert insufficient_funds_2.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL, '#2 event type is not INSUFFICIENT_FUNDS_EMAIL'
    assert insufficient_funds_2.user_id == user.user_id, '#2 user_id'
    assert insufficient_funds_2.state == EventOutState.READY, '#2 state is not SUPPRESSED'
    assert insufficient_funds_2.linked_in_events_ids == [payment_failed_2.event_id], '#2 linked_in_events_ids'