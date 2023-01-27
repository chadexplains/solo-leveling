import datetime


class UtcTime:

    format = "%Y-%m-%d %H:%M:%S%z"

    def __init__(self, value):
        self.value = value.astimezone(datetime.timezone.utc)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __str__(self):
        return self.value.strftime(self.format)

    @classmethod
    def of_string(cls, s: str):
        return cls(value=datetime.datetime.strptime(s, cls.format))

    def diff_to_nearest_second(self, other):
        unrounded = self.value - other.value
        return datetime.timedelta(seconds=round(unrounded.total_seconds(), 0))

    @classmethod
    def now(cls):
        return cls(value=datetime.datetime.now())
