from __future__ import annotations

from abc import ABC, abstractmethod

from src.domains import EventIn, EventOut, User

event_strategies: list[type[BaseStrategy]] = []


class BaseStrategy(ABC):

    # TODO: по умолчанию включаем все стратегии в список
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        event_strategies.append(cls)

    # TODO: определиться с неймингом!!!
    @staticmethod
    @abstractmethod
    def extend_out_event(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs):
        # На основе всех входящих, исходящих и доп.данных (юзер) решить,
        # какие события должны быть порождены на выходе
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def judge_out_event(out_events: set[EventOut], **kwargs):
        # На основе существующих исходящих событий, времени, настроек в отдельной стране и т.п. решить,
        # какие события должны быть подавлены и проигнорированы.
        raise NotImplementedError