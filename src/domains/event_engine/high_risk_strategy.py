from src.models import EventIn, EventOut, User, EventInType, EventOutType, EventOutState
from src.domains.event_engine import BaseStrategy


EXPLANATION_TEMPLATE_OK = 'High risk! {limit} payment attempts failed (in event ids: {in_event_ids})'
EXPLANATION_TEMPLATE_SUPPRESSED = 'Alert message already exists (exist out event_id: {out_event_id})'
HIGH_RISK_ALERT_LIMIT = 3


class WelcomeStrategy(BaseStrategy):

    @staticmethod
    def extend_out_event(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs) -> set[EventOut]:
        # If payment_failed with attempt_number >= 3, escalate to “HIGH_RISK_ALERT”
        created_out_events: set[EventOut] = set()

        # get in events linked with payment
        payment_in_events = sorted(
            {e for e in in_events if e.event_type in {EventInType.PAYMENT_FAILED, EventInType.PAYMENT_INITIATED}},
            key=lambda e: e.timestamp,
        )
        payment_failed_in_row = []
        for in_event in reversed(payment_in_events):
            # successful payment => previous failed payments don't have impact
            if in_event.event_type == EventInType.PAYMENT_INITIATED:
                break

            # TODO: тест-кейсы:
            #  1. череда из 3 фейлов, успешная оплата, снова череда фейлов - событие генерируется;
            #  2. череда из 4 фейлов - событие о рисках одно;
            #  3. 2 фейла, 1 успех, 2 фейла - событий нет.
            # remember attempts of failed payments
            elif in_event.event_type == EventInType.PAYMENT_FAILED:
                payment_failed_in_row.append(in_event)

                if len(payment_failed_in_row) >= HIGH_RISK_ALERT_LIMIT:
                    tmp_out_event = EventOut.factory(
                        linked_in_events=payment_failed_in_row,
                        user=user,
                        event_type=EventOutType.HIGH_RISK_ALERT,
                    )
                    # add only brand-new events
                    if tmp_out_event not in out_events:
                        created_out_events.add(tmp_out_event)

        # extend already exist out events
        out_events |= created_out_events

        return created_out_events

    @staticmethod
    def judge_out_event(in_events: list[EventIn], out_events: set[EventOut], **kwargs) -> None:
        # get the last payment_inited event
        last_payment_inited_in_event = max(
            (e for e in in_events if e.event_type == EventInType.PAYMENT_INITIATED),
            key=lambda e: e.event_timestamp,
            default=None,
        )

        # get high_risk out events which happen after last payment_inited in event
        high_risk_out_events = {
            e for e in out_events
            if e.event_type == EventOutType.HIGH_RISK_ALERT and e.event_timestamp > last_payment_inited_in_event.event_timestamp
        }
        if not high_risk_out_events:
            return

        # get the last existing out event
        last_in_pipeline_event = max(
            (e for e in high_risk_out_events if e.is_in_pipeline),
            key=lambda e: e.event_timestamp,
            default=None,
        )

        # choose the last created out event, if we don't have any ready/processing/done event
        if last_in_pipeline_event is None:
            last_in_pipeline_event = max(
                (e for e in high_risk_out_events if e.state == EventOutState.CREATED),  # last event in CREATED state
                key=lambda e: e.event_timestamp,
                default=None,
            )
            last_in_pipeline_event.state = EventOutState.READY
            last_in_pipeline_event.explanation = EXPLANATION_TEMPLATE_OK.format(
                limit=HIGH_RISK_ALERT_LIMIT,
                in_event_ids=last_in_pipeline_event.linked_in_events,
            )

        # suppress other out events which were happen after last payment inited
        high_risk_out_events.discard(last_in_pipeline_event)
        for event in high_risk_out_events:
            event.state = EventOutState.SUPPRESSED
            event.explanation = EXPLANATION_TEMPLATE_SUPPRESSED.format(out_event_id=last_in_pipeline_event.event_id)
