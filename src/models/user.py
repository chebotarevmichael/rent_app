from enum import Enum

from src.models import Base


class UserRiskSegment(str, Enum):
    LIGHT = 'LIGHT'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


class User(Base):
    user_id: str
    email: str | None
    country: str | None
    marketing_opt_in: bool
    risk_segment: UserRiskSegment

    # TODO: add email validator
    # TODO: add country validator

    @property
    def db_id(self):
        return self.user_id

