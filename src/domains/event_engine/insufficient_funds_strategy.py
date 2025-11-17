from src.models import EventIn, EventOut, User, EventInType, EventOutType, EventOutState
from src.domains.event_engine import BaseStrategy
from src.tools import is_same_utc_day

EXPLANATION_TEMPLATE_OK = 'Remind message was approved (in event ids: {in_event_ids})'
EXPLANATION_TEMPLATE_SUPPRESSED = 'Remind message already happen today (exist out event_id: {out_event_id})'
DELAY_BETWEEN_SIGNUP_COMPLETED_AND_LINK_BANK_SUCCESS_SEC = 24 * 60 * 60


class InsufficientFundsStrategy(BaseStrategy):

    @staticmethod
    def extend_out_event(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs) -> set[EventOut]:
        # If payment_failed with failure_reason == "INSUFFICIENT_FUNDS", send “INSUFFICIENT_FUNDS_EMAIL`,
        # BUT only once per user per calendar day.
        created_out_events: set[EventOut] = set()

        for in_event in in_events:
            # ignore in events with another type
            if in_event.event_type != EventInType.PAYMENT_FAILED:
                continue

            tmp_out_event = EventOut.factory(
                linked_in_events=[in_event],  # payment failed
                user=user,
                event_type=EventOutType.INSUFFICIENT_FUNDS_EMAIL,
            )
            # add only brand-new events
            if tmp_out_event not in out_events:
                created_out_events.add(tmp_out_event)

        # extend already exist out events
        out_events |= created_out_events

        return created_out_events

    @staticmethod
    def judge_out_event(in_events: list[EventIn], out_events: set[EventOut], **kwargs) -> None:
        # ignore other
        bank_link_out_events = {e for e in out_events if e.event_type == EventOutType.INSUFFICIENT_FUNDS_EMAIL}
        if not bank_link_out_events:
            return

        # get an actual existing out event
        in_pipeline_event = max(
            (e for e in bank_link_out_events if e.is_in_pipeline and is_same_utc_day(ts=e.event_timestamp)),
            key=lambda e: e.event_timestamp,
            default=None,
        )

        # choose something, if we don't have any ready/processing/done event on this calendar day
        if in_pipeline_event is None:
            in_pipeline_event = bank_link_out_events.pop()  # event in CREATED state
            in_pipeline_event.state = EventOutState.READY
            in_pipeline_event.explanation = EXPLANATION_TEMPLATE_OK.format(in_event_ids=in_pipeline_event.linked_in_events_ids)

        # suppress other
        bank_link_out_events.discard(in_pipeline_event)
        for event in bank_link_out_events:
            event.state = EventOutState.SUPPRESSED
            event.explanation = EXPLANATION_TEMPLATE_SUPPRESSED.format(out_event_id=in_pipeline_event.event_id)
