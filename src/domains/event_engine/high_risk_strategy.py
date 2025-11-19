from datetime import datetime

from src.models import EventIn, EventOut, User, EventInType, EventOutType, EventOutState, EventOutChannel
from src.domains.event_engine import BaseStrategy


MESSAGE_TEMPLATE = 'User (user_id={user_id}) has >= {limit} failed payments. Previous successful payment: {ts}'
EXPLANATION_TEMPLATE_OK = 'High risk! {limit} payment attempts failed (in event ids: {in_event_ids})'
EXPLANATION_TEMPLATE_SUPPRESSED = 'Alert message already exists (exist out event_id: {out_event_id})'
HIGH_RISK_ALERT_LIMIT = 3


class HighRiskStrategy(BaseStrategy):
    @staticmethod
    def get_last_initiated_ts(in_events: list[EventIn]) -> datetime | None:
        return max(
            (e.event_timestamp for e in in_events if e.event_type == EventInType.PAYMENT_INITIATED),
            default=None,
        )

    @staticmethod
    def extend_out_event(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs) -> set[EventOut]:
        # If payment_failed with attempt_number >= 3, escalate to “HIGH_RISK_ALERT”
        created_out_events: set[EventOut] = set()

        # get timestamp of the last successful payment
        last_initiated_ts = HighRiskStrategy.get_last_initiated_ts(in_events=in_events)

        # get only "payment failed" events, which happened after the last successful payment
        payment_failed_in_events = []
        for in_event in in_events:
            # skip other type
            if in_event.event_type != EventInType.PAYMENT_FAILED:
                continue
            # skip payment failed events BEFORE payment_initiated (if it exists)
            if last_initiated_ts and last_initiated_ts > in_event.event_timestamp:
                continue
            payment_failed_in_events.append(in_event)

        payment_failed_in_row = []
        for in_event in sorted(payment_failed_in_events, key=lambda e: e.event_timestamp):
            payment_failed_in_row.append(in_event)

            # TODO: можно переделать под attempt_number, тогда не придется опираться на "сколько событий дошло"

            if len(payment_failed_in_row) >= HIGH_RISK_ALERT_LIMIT:
                tmp_out_event = EventOut.factory(
                    message=HighRiskStrategy.build_message(user=user, last_initiated_ts=last_initiated_ts),
                    linked_in_events=payment_failed_in_row,
                    user=user,
                    event_type=EventOutType.HIGH_RISK_ALERT,
                    channel=EventOutChannel.INTERNAL_ALERT,
                    event_timestamp=kwargs.get('_now'),
                )
                # add only brand-new events
                if tmp_out_event not in out_events:
                    created_out_events.add(tmp_out_event)

        # extend already exist out events
        out_events |= created_out_events

        return created_out_events

    @staticmethod
    def judge_out_event(in_events: list[EventIn], out_events: set[EventOut], **kwargs) -> None:
        # get timestamp of the last successful payment
        last_initiated_ts = HighRiskStrategy.get_last_initiated_ts(in_events=in_events)

        # get high_risk out events which happened after last payment_inited in event
        high_risk_out_events = set()
        for out_event in out_events:
            # skip other type
            if out_event.event_type != EventOutType.HIGH_RISK_ALERT:
                continue
            # skip high risk out events BEFORE payment_initiated (if it exists)
            if last_initiated_ts and out_event.event_timestamp < last_initiated_ts:
                continue
            # there are high risk events which happened AFTER last successful payment
            high_risk_out_events.add(out_event)

        if not high_risk_out_events:
            return

        # get the LAST existing high risk out event
        in_pipeline_event = max(
            (e for e in high_risk_out_events if e.is_in_pipeline),
            key=lambda e: e.event_timestamp,
            default=None,
        )

        # choose the FIRST created out event, if we don't have any ready/processing/done event
        if in_pipeline_event is None:
            in_pipeline_event = min(
                (e for e in high_risk_out_events if e.state == EventOutState.CREATED),  # FIRST event in CREATED state
                key=lambda e: e.event_timestamp,
                default=None,
            )
            in_pipeline_event.state = EventOutState.READY
            in_pipeline_event.explanation = EXPLANATION_TEMPLATE_OK.format(
                limit=HIGH_RISK_ALERT_LIMIT,
                in_event_ids=in_pipeline_event.linked_in_events_ids,
            )

        # suppress other out events which were happened after last payment inited
        high_risk_out_events.discard(in_pipeline_event)
        for event in high_risk_out_events:
            event.state = EventOutState.SUPPRESSED
            event.explanation = EXPLANATION_TEMPLATE_SUPPRESSED.format(out_event_id=in_pipeline_event.event_id)

    @staticmethod
    def build_message(user: User, last_initiated_ts: datetime) -> str:
        return MESSAGE_TEMPLATE.format(
            user_id=user.user_id,
            limit=HIGH_RISK_ALERT_LIMIT,
            ts=last_initiated_ts,
        )
