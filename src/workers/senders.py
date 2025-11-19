import dramatiq

from src.models import EventOut


@dramatiq.actor(max_retries=5)
def send_event_out(event_id: str):
    event: EventOut = EventOut.get(db_id=event_id)
    if not event:
        return

    event.execute()

