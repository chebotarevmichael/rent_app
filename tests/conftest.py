import uuid

import pytest

from datetime import datetime, timezone

from src.models import User, EventIn, Base, EventInType, EventOutType, EventOutType


# TODO: надо ли оно мне вообще?
@pytest.fixture(autouse=True)
def clean_db():
    """Очищает in-memory DB перед каждым тестом."""
    Base._db.clear()
    yield
    Base._db.clear()


@pytest.fixture
def user():
    """
    Создаёт юзера с дефолтными параметрами.
    Можно перегружать аргументы:
        user(user_id='u_123', marketing_opt_in=False)
    """
    def _create_user(**overrides):
        _user_id = str(uuid.uuid4())
        data = {
            'user_id': _user_id,
            'email': f'{_user_id}@example.com',
            'country': 'US',
            'marketing_opt_in': True,
            'risk_segment': 'LOW',
        }

        data.update(overrides)

        u = User(**data)
        u.save()
        return u

    return _create_user


@pytest.fixture
def event_in(user):
    """
    Создаёт EventIn с дефолтными значениями.
    Можно перегружать:
        event_in(event_type=..., properties=...)
    """
    def _create_event(
        event_type: EventInType = EventInType.SIGNUP_COMPLETED,
        user_id: str = None,
        event_timestamp: datetime = None,
        **overrides,
    ):
        if user_id is None:
            user_id = overrides.pop('user', user()).user_id

        data = {
            'event_type': event_type,
            'user_id': user_id,
            'event_timestamp': event_timestamp or datetime.now(tz=timezone.utc),
            'properties': {},
        }
        data.update(overrides)

        _event_in = EventIn.factory(**data)
        _event_in.save()
        return _event_in

    return _create_event
