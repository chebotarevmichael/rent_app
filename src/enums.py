from enum import Enum


class EventInType(str, Enum):
    SIGNUP_COMPLETED = 'SIGNUP_COMPLETED'
    LINK_BANK_SUCCESS = 'LINK_BANK_SUCCESS'
    PAYMENT_INITIATED = 'PAYMENT_INITIATED'
    PAYMENT_FAILED = 'PAYMENT_FAILED'


class EventOutType(str, Enum):
    WELCOME_EMAIL = 'WELCOME_EMAIL'
    BANK_LINK_NUDGE_SMS = 'BANK_LINK_NUDGE_SMS'
    INSUFFICIENT_FUNDS_EMAIL = 'INSUFFICIENT_FUNDS_EMAIL'
    HIGH_RISK_ALERT = 'HIGH_RISK_ALERT'


class EventOutState(str, Enum):
    # only in memory, this state can not be in DB
    # TODO: в реальной жизни этого статуса бы не было, в таблице state IS NOT NULL, а у энтити state при создании был бы None.
    #  но т.к. в текущем коде не схемы БД, сделал статус в явном виде, иначе было бы не понятно.
    CREATED = 'CREATED'

    # processing
    READY = 'READY'
    PROCESSING = 'PROCESSING'

    # finished
    DONE = 'DONE'
    SUPPRESSED = 'SUPPRESSED'


class RiskSegment(str, Enum):
    LIGHT = 'LIGHT'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
