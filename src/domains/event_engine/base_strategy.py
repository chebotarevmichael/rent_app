from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import EventIn, EventOut, User

event_strategies: list[type[BaseStrategy]] = []


class BaseStrategy(ABC):

    # todo NOTE:
    #  По умолчанию включаем все стратегии в список, и осознано идем на допущение, что мы не управляем
    #  какая из стратегий вкл/выкл (по умолчанию все ВКЛ).
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        event_strategies.append(cls)

    @staticmethod
    @abstractmethod
    def extend_out_events(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs):
        """Based on all incoming, outgoing and **kwargs to decide which events should be generated at the output."""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def judge_out_events(in_events: list[EventIn], out_events: set[EventOut], **kwargs):
        """Based on all incoming, outgoing and **kwargs TO decide which events should be suppressed and ignored."""
        raise NotImplementedError
