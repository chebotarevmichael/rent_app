from datetime import datetime, timezone, timedelta

from src.models import EventOut, EventOutType, EventInType, EventOutState
from src.scripts.cron import cron_generate_out_events
from src.tools import now

from tests.conftest import user, event_in


def test_basic(user, event_in):
    _ = "Базовый тест. 2 провала оплаты - ничего, на 3ий - событие high risk"

    _now = now()

    # build input data
    user = user()
    payment_failed_1 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=1), user=user)
    payment_failed_2 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=2), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # no high risk events
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 0, 'no events'

    # yet another payment_failed input event
    payment_failed_3 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=3), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])

    assert len(out_events) == 1, 'out event: high_risk'

    high_risk, *_ = out_events
    assert high_risk.event_type == EventOutType.HIGH_RISK_ALERT, 'event type is not HIGH_RISK_ALERT'
    assert high_risk.user_id == user.user_id, 'user_id'
    assert high_risk.state == EventOutState.READY, 'state is not READY'
    assert high_risk.linked_in_events_ids == [
        payment_failed_1.event_id, payment_failed_2.event_id, payment_failed_3.event_id
    ], 'linked_in_events_ids'



def test_saving_by_payment_inited(user, event_in):
    _ = "2 провала оплаты, 1 успешная; через 1 месяц еще 2 провала оплаты, но события high risk нету"

    _now = now()

    # build input data
    user = user()
    event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=1), user=user)
    event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=2), user=user)
    event_in(event_type=EventInType.PAYMENT_INITIATED, event_timestamp=_now + timedelta(hours=3), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # no high risk events
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 0, 'no event'

    # yet another payment_failed input event
    event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(days=30), user=user)
    event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(days=31), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # check the result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    assert len(out_events) == 0, 'still no event'


def test_old_payment_inited_not_saved(user, event_in):
    _ = "1 успешная месяц назад; 3 провала оплаты сейчас, поэтому событие high risk есть"

    _now = now()

    # build input data
    user = user()

    event_in(event_type=EventInType.PAYMENT_INITIATED, event_timestamp=_now - timedelta(days=30), user=user)

    payment_failed_1 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=1), user=user)
    payment_failed_2 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=2), user=user)
    payment_failed_3 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=3), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])

    assert len(out_events) == 1, 'high risk x1'

    high_risk, *_ = out_events
    assert high_risk.event_type == EventOutType.HIGH_RISK_ALERT, 'event type is not HIGH_RISK_ALERT'
    assert high_risk.user_id == user.user_id, 'user_id'
    assert high_risk.state == EventOutState.READY, 'state is not READY'
    assert high_risk.linked_in_events_ids == [
        payment_failed_1.event_id, payment_failed_2.event_id, payment_failed_3.event_id
    ], 'linked_in_events_ids'


def test_payment_failed_x4(user, event_in):
    _ = "4 провала оплаты, есть 2 события high risk"

    _now = now()

    # build input data
    user = user()

    payment_failed_1 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=1), user=user)
    payment_failed_2 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=2), user=user)
    payment_failed_3 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=3), user=user)
    payment_failed_4 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now + timedelta(hours=4), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort()

    assert len(out_events) == 2, 'high risk x2'

    high_risk_1, high_risk_2 = out_events

    # high_risk_1 (READY)
    assert high_risk_1.event_type == EventOutType.HIGH_RISK_ALERT, '#1 event type is not HIGH_RISK_ALERT'
    assert high_risk_1.user_id == user.user_id, '#1 user_id'
    assert high_risk_1.state == EventOutState.READY, '#1 state is not READY'
    assert high_risk_1.linked_in_events_ids == [
        payment_failed_1.event_id, payment_failed_2.event_id, payment_failed_3.event_id
    ], '#1 linked_in_events_ids'

    # high_risk_2 (SUPPRESSED)
    assert high_risk_2.event_type == EventOutType.HIGH_RISK_ALERT, '#2 event type is not HIGH_RISK_ALERT'
    assert high_risk_2.user_id == user.user_id, '#2 user_id'
    assert high_risk_2.state == EventOutState.SUPPRESSED, '#2 state is not SUPPRESSED'
    assert high_risk_2.linked_in_events_ids == [
        payment_failed_1.event_id, payment_failed_2.event_id, payment_failed_3.event_id, payment_failed_4.event_id
    ], '#2 linked_in_events_ids'


def test_payment_failed_twice_but_not_suppressed(user, event_in):
    _ = "3 провала оплаты, 1 событие high risk, потом была оплата и снова 3 провала оплаты - должен быть high risk #2"

    #
    # === User failed 3 payments, but finally he paid ==
    _now = now()

    # build input data
    user = user()

    payment_failed_1 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now - timedelta(hours=3), user=user)
    payment_failed_2 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now - timedelta(hours=2), user=user)
    payment_failed_3 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_now - timedelta(hours=1), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort()

    assert len(out_events) == 1, 'high risk x1'

    #
    # === AFTER 1 MONTH, User again failed 3 payments ==
    high_risk_1, *_ = out_events
    event_in(event_type=EventInType.PAYMENT_INITIATED, event_timestamp=_now + timedelta(hours=10), user=user)

    _next_month = now() + timedelta(days=30)

    payment_failed_4 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_next_month + timedelta(hours=1), user=user)
    payment_failed_5 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_next_month + timedelta(hours=2), user=user)
    payment_failed_6 = event_in(event_type=EventInType.PAYMENT_FAILED, event_timestamp=_next_month + timedelta(hours=3), user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id], _now=_next_month + timedelta(hours=1))

    # result
    out_events: list[EventOut] = EventOut.bulk_get_by_user_ids(user_ids=[user.user_id])
    out_events.sort()

    assert len(out_events) == 2, 'high risk x2'

    high_risk_1, high_risk_2 = out_events

    # high_risk_1 (READY)
    assert high_risk_1.event_type == EventOutType.HIGH_RISK_ALERT, '#1 event type is not HIGH_RISK_ALERT'
    assert high_risk_1.user_id == user.user_id, '#1 user_id'
    assert high_risk_1.state == EventOutState.READY, '#1 state is not READY'
    assert high_risk_1.linked_in_events_ids == [
        payment_failed_1.event_id, payment_failed_2.event_id, payment_failed_3.event_id
    ], '#1 linked_in_events_ids'

    # high_risk_2 (READY #2)
    assert high_risk_2.event_type == EventOutType.HIGH_RISK_ALERT, '#2 event type is not HIGH_RISK_ALERT'
    assert high_risk_2.user_id == user.user_id, '#2 user_id'
    assert high_risk_2.state == EventOutState.READY, '#2 state is not READY'
    assert high_risk_2.linked_in_events_ids == [
        payment_failed_4.event_id, payment_failed_5.event_id, payment_failed_6.event_id
    ], '#2 linked_in_events_ids'
