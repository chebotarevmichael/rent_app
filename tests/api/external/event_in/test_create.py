from datetime import datetime
from typing import Any

from fastapi.testclient import TestClient

from src.main import app
from src.models import EventIn, User, EventInType
from src.tools import now, gen_id

client = TestClient(app)


def _get_payload(
    user_id: str | Any = None,
    event_type: EventInType | Any = None,
    event_timestamp: datetime | Any = None,
    failure_reason: str | Any = None,
    user_email: str | Any = None,
):
    return {
        'user_id': user_id or gen_id(),
        'event_type': event_type or 'payment_failed',
        'event_timestamp': str(event_timestamp or now()),
        'properties': {
            'amount': 1425.00,
            'attempt_number': 2,
            'failure_reason': failure_reason or 'INSUFFICIENT_FUNDS',
        },
        'user_traits': {
            'email': user_email or 'maria@example.com',
            'country': 'PT',
            'marketing_opt_in': True,
            'risk_segment': 'MEDIUM',
        },
    }


def test_create_event_success():
    payload = _get_payload()

    resp = client.post('/api/external/event_in/create', json=payload)

    # ok
    assert resp.status_code == 200
    data = resp.json()
    user_id = data['user_id']
    assert data['user_id'] == user_id
    assert data['event_type'] == payload['event_type']
    assert data['stored'] is True
    assert 'event_id' in data

    # event was created
    event = EventIn.get(db_id=data['event_id'])
    assert event is not None
    assert event.user_id == user_id
    assert event.event_type.value == payload['event_type']
    assert event.properties['failure_reason'] == 'INSUFFICIENT_FUNDS'

    # user was created
    user = User.get(db_id=user_id)
    assert user is not None
    assert user.email == payload['user_traits']['email']
    assert user.country == payload['user_traits']['country']
    assert user.marketing_opt_in is True


def test_repeated_event():
    user_id = gen_id()
    event_timestamp = now()

    payload = _get_payload(user_id=user_id, event_timestamp=event_timestamp)

    resp = client.post('/api/external/event_in/create', json=payload)

    # first event was created
    assert resp.status_code == 200, 'status_code'
    data = resp.json()
    assert data['user_id'] == user_id, 'user_id'

    event = EventIn.get(db_id=data['event_id'])
    assert event, 'event was created'

    # but the second wasn't
    resp = client.post('/api/external/event_in/create', json=payload)
    assert resp.status_code == 400
    detail = resp.json()['detail']
    assert detail['error'] == 'Duplicated input event', 'error text'
    assert detail['user_id'] == user_id, 'user_id'
    assert detail['event_id'] == f'EventInType.PAYMENT_FAILED:{user_id}:{event_timestamp.isoformat()}', 'event_id'


def test_4_different_events_at_same_time():
    user_id = 'user_test_same_time'
    event_timestamp = '2025-11-19T14:12:18.990218+00:00'

    for event_type in list(EventInType):
        payload = _get_payload(user_id=user_id, event_timestamp=event_timestamp, event_type=event_type)
        resp = client.post('/api/external/event_in/create', json=payload)
        assert resp.status_code == 200, 'status_code'

    events = EventIn.bulk_get(
        db_ids=[
            f'{event_type}:{user_id}:{event_timestamp}'
            for event_type in list(EventInType)
        ]
    )
    assert len(events) == 4, '4 events were created'


def test_2_similar_events_for_2_user():
    user_id_1 = 'test_2_similar_events_for_2_user_1'
    user_id_2 = 'test_2_similar_events_for_2_user_2'
    event_timestamp = '2025-11-19T14:12:18.990218+00:00'

    # user_1
    payload = _get_payload(user_id=user_id_1, event_timestamp=event_timestamp, event_type=EventInType.LINK_BANK_SUCCESS)
    resp = client.post('/api/external/event_in/create', json=payload)
    assert resp.status_code == 200, 'status_code'

    # user_2
    payload = _get_payload(user_id=user_id_2, event_timestamp=event_timestamp, event_type=EventInType.LINK_BANK_SUCCESS)
    resp = client.post('/api/external/event_in/create', json=payload)
    assert resp.status_code == 200, 'status_code'

    events = EventIn.bulk_get(
        db_ids=[
            f'{EventInType.LINK_BANK_SUCCESS}:{user_id_1}:{event_timestamp}',
            f'{EventInType.LINK_BANK_SUCCESS}:{user_id_2}:{event_timestamp}',
        ]
    )
    assert len(events) == 2, '2 events were created'


def test_update_user():
    user_id = 'test_2_similar_events_for_2_user_1'

    # create
    user_email_v1 = 'user_v1@example.com'
    payload_create_1 = _get_payload(user_id=user_id, user_email=user_email_v1)
    resp = client.post('/api/external/event_in/create', json=payload_create_1)

    assert resp.status_code == 200, 'OK'
    user_v1 = User.get(db_id=user_id)
    assert user_v1 is not None, 'user created'
    assert user_v1.email == user_email_v1, 'email #1'
    assert user_v1.country == payload_create_1['user_traits']['country']
    assert user_v1.marketing_opt_in is True

    # update with user changes
    user_email_v2 = 'user_v2@root.org'
    payload_update_v2 = _get_payload(user_id=user_id, user_email=user_email_v2)
    resp = client.post('/api/external/event_in/create', json=payload_update_v2)

    assert resp.status_code == 200, 'OK'
    user_v2 = User.get(db_id=user_id)
    assert user_v2 is not None, 'user updated'
    assert user_v2.email == user_email_v2, 'email #2'
    assert user_v2.country == payload_update_v2['user_traits']['country']
    assert user_v2.marketing_opt_in is True

    # update with NO user changes
    payload_update_v3 = _get_payload(user_id=user_id, user_email=user_email_v2)
    resp = client.post('/api/external/event_in/create', json=payload_update_v3)

    assert resp.status_code == 200, 'OK'
    user_v3 = User.get(db_id=user_id)
    assert user_v3 is not None, 'user created'
    assert user_v2 is user_v3, 'user was not updated'
