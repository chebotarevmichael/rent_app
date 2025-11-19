from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import EventIn, EventOut, User

event_strategies: list[type[BaseStrategy]] = []


class BaseStrategy(ABC):

    # TODO: NOTE
    #  По умолчанию включаем все стратегии в список, и осознано идем на допущение, что мы не управляем
    #  какая из стратегий вкл/выкл (по умолчанию все ВКЛ).
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        event_strategies.append(cls)

    @staticmethod
    @abstractmethod
    def extend_out_events(in_events: list[EventIn], out_events: set[EventOut], user: User, **kwargs):
        # На основе всех входящих, исходящих и доп.данных (юзер) решить,
        # какие события должны быть порождены на выходе
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def judge_out_events(in_events: list[EventIn], out_events: set[EventOut], **kwargs):
        # На основе существующих исходящих событий, времени, настроек в отдельной стране и т.п. решить,
        # какие события должны быть подавлены и проигнорированы.
        raise NotImplementedError
