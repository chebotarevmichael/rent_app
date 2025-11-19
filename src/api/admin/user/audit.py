from src.api.utils import build_router
from src.api.exceptions import NotFound
from src.models import EventIn, EventOut, User

router = build_router(__name__)

MAX_AMOUNT_OF_EVENTS = 100


@router.get('/audit/{user_id}')
async def audit(user_id: str):
    user = User.get(db_id=user_id)
    if not user:
        raise NotFound('User not found', user_id=user_id)

    return {
        'user': {
            'user_id': user.user_id,
            'email': user.email,
            'country': user.country,
            'marketing_opt_in': user.marketing_opt_in,
            'risk_segment': user.risk_segment.value,
        },
        'events_in': sorted(EventIn.bulk_get_by_user_ids([user_id]))[-MAX_AMOUNT_OF_EVENTS:],
        'events_out': sorted(EventOut.bulk_get_by_user_ids([user_id]))[-MAX_AMOUNT_OF_EVENTS:],
    }
