from datetime import datetime
from enum import Enum

from pydantic import EmailStr

from src.models import Base


class UserRiskSegment(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'


class User(Base):
    user_id: str
    email: EmailStr | None
    country: str | None
    marketing_opt_in: bool
    risk_segment: UserRiskSegment

    # todo: add country validator

    @property
    def db_id(self):
        return self.user_id
