from src.domains import BaseEntity
from src.enums import RiskSegment


class User(BaseEntity):
    user_id: str
    email: str | None
    country: str | None
    marketing_opt_in: bool
    risk_segment: RiskSegment

    # TODO: add email validator
    # TODO: add country validator

    @property
    def db_id(self):
        return self.user_id

