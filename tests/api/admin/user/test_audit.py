from fastapi.testclient import TestClient

from src.main import app
from src.models import EventInType
from src.scripts.cron import cron_generate_out_events
from tests.conftest import user, event_in

client = TestClient(app)


def test_basic(user, event_in):
    _ = 'Слишком базовый тест. 1 входящее и 1 исходящее'

    # build input data
    user = user()
    event_in(event_type=EventInType.SIGNUP_COMPLETED, user=user)

    # call strategy
    cron_generate_out_events(actual_users_ids=[user.user_id])

    # call audit
    resp = client.get(f'/api/admin/user/audit/{user.user_id}')
    assert resp.status_code == 200

    data = resp.json()

    # light check
    assert data['user']['user_id'] == user.user_id
    assert len(data['events_in']) == 1, '1 на входе'
    assert len(data['events_out']) == 1, '1 на выходе'
