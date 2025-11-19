from src.models import EventIn, EventOut, User, EventInType, EventOutType, EventOutState, EventOutChannel
from src.domains.event_engine import BaseStrategy


MESSAGE_TEMPLATE = 'Welcome to Derry!'
EXPLANATION_TEMPLATE_OK = 'Welcome message was approved (in event ids: {in_event_ids})'
EXPLANATION_TEMPLATE_SUPPRESSED = 'Welcome message already exists (exist out event_id: {out_event_id})'


class WelcomeStrategy(BaseStrategy):

    @staticmethod
    def extend_out_events(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs) -> set[EventOut]:
        # If signup_completed AND user_traits.marketing_opt_in == true, send the “WELCOME_EMAIL”.
        created_out_events: set[EventOut] = set()

        if not user.marketing_opt_in:
            return created_out_events

        for in_event in in_events:
            if in_event.event_type == EventInType.SIGNUP_COMPLETED:
                tmp_out_event = EventOut.factory(
                    message=MESSAGE_TEMPLATE,
                    linked_in_events=[in_event],
                    user=user,
                    event_type=EventOutType.WELCOME_EMAIL,
                    channel=EventOutChannel.EMAIL,
                    _now=kwargs.get('_now'),
                )
                # add only brand-new events
                if tmp_out_event not in out_events:
                    created_out_events.add(tmp_out_event)

        # extend already exist out events
        out_events |= created_out_events

        return created_out_events

    @staticmethod
    def judge_out_events(in_events: list[EventIn], out_events: set[EventOut], **kwargs) -> None:
        # ignore other
        welcome_out_events = {e for e in out_events if e.event_type == EventOutType.WELCOME_EMAIL}
        if not welcome_out_events:
            return

        # get any actual existing out event
        in_pipeline_event = next((e for e in welcome_out_events if e.is_in_pipeline), None)

        # choose something, if we don't have any ready/processing/done event
        if in_pipeline_event is None:
            in_pipeline_event = min(welcome_out_events) # the earliest event in CREATED state
            in_pipeline_event.state = EventOutState.READY
            in_pipeline_event.explanation = EXPLANATION_TEMPLATE_OK.format(in_event_ids=in_pipeline_event.linked_in_events_ids)

        # suppress other
        welcome_out_events.discard(in_pipeline_event)
        for event in welcome_out_events:
            event.state = EventOutState.SUPPRESSED
            event.explanation = EXPLANATION_TEMPLATE_SUPPRESSED.format(out_event_id=in_pipeline_event.event_id)

        # todo NOTE: в текущей парадигме изменение уже существующих в БД событий недопустимо (заточка под CH)
        #  в БД будут записываться только те, что созданы только что в extend_out_event(...)
        #  .
        #  Если мы хотим обновить out-события, возможно нам просто нужна новая стратегия, которая порождает какое-то
        #  аут_событие_2 на основе аут_событие_1. И не пробовать сделать все в рамках стратегии породившей аут_событие_1