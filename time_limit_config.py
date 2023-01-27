import datetime


class TimeLimitConfig:
    def __init__(
        self,
        design: datetime.timedelta,
        code: datetime.timedelta,
        unclaimed_review: datetime.timedelta,
        claimed_review: datetime.timedelta,
    ):
        self.design = design
        self.code = code
        self.unclaimed_review = unclaimed_review
        self.claimed_review = claimed_review
