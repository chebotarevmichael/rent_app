from src.models import EventIn, EventOut, User, EventInType, EventOutType, EventOutState
from src.domains.event_engine import BaseStrategy


EXPLANATION_TEMPLATE_OK = 'Nudge SMS was approved (in event ids: {in_event_ids})'
EXPLANATION_TEMPLATE_SUPPRESSED = 'Nudge SMS already exists (exist out event_id: {out_event_id})'
DELAY_BETWEEN_SIGNUP_COMPLETED_AND_LINK_BANK_SUCCESS_SEC = 24 * 60 * 60


class ReadyToPayStrategy(BaseStrategy):

    @staticmethod
    def extend_out_event(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs) -> set[EventOut]:
        # If link_bank_success within 24h of signup_completed, send “BANK_LINK_NUDGE_SMS”
        created_out_events: set[EventOut] = set()

        # TODO: вообще по идее, мы должны здесь выбрать ВСЕ signup_completed-события и ВСЕ link_bank_success-события,
        #  и построить декартово произведение, чтобы увидеть все-все потенциальные исходящие bank_link_nudge_sms-события.
        #  .
        #  Взял на себя смелость ограничиться последним signup_completed-событием, чтобы не плодить лишние out-события.
        last_signup_completed_in_event = max(
            (e for e in in_events if e.event_type == EventInType.SIGNUP_COMPLETED),
            key=lambda e: e.event_timestamp,
            default=None,
        )

        # signup is not completed => go away
        if last_signup_completed_in_event is None:
            return created_out_events

        for in_event in in_events:
            # ignore in events with another type
            if in_event.event_type != EventInType.LINK_BANK_SUCCESS:
                continue

            # the delay between both event must be less than required
            _delta = last_signup_completed_in_event.event_timestamp - in_event.event_timestamp
            if abs(_delta.total_seconds()) > DELAY_BETWEEN_SIGNUP_COMPLETED_AND_LINK_BANK_SUCCESS_SEC:
                continue

            tmp_out_event = EventOut.factory(
                linked_in_events=[last_signup_completed_in_event, in_event], # signup_completed + link_bank_success
                user=user,
                event_type=EventOutType.BANK_LINK_NUDGE_SMS,
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
        bank_link_out_events = {e for e in out_events if e.event_type == EventOutType.BANK_LINK_NUDGE_SMS}
        if not bank_link_out_events:
            return

        # get an actual existing out event
        in_pipeline_event = next((e for e in bank_link_out_events if e.is_in_pipeline), None)

        # choose something, if we don't have any ready/processing/done event
        if in_pipeline_event is None:
            in_pipeline_event = min(
                bank_link_out_events,
                key=lambda e: e.event_timestamp,    # the earliest event in CREATED state
            )
            in_pipeline_event.state = EventOutState.READY
            in_pipeline_event.explanation = EXPLANATION_TEMPLATE_OK.format(in_event_ids=in_pipeline_event.linked_in_events_ids)

        # suppress other
        bank_link_out_events.discard(in_pipeline_event)
        for event in bank_link_out_events:
            event.state = EventOutState.SUPPRESSED
            event.explanation = EXPLANATION_TEMPLATE_SUPPRESSED.format(out_event_id=in_pipeline_event.event_id)