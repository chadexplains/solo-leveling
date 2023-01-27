import datetime

from utc_time import UtcTime


def arbitrary_date_in_timezone(timezone: datetime.timezone):
    return UtcTime(datetime.datetime(year=2022, month=1, day=1, tzinfo=timezone))


def run_of_string(s: str, expected: UtcTime):
    assert UtcTime.of_string(s) == expected


def of_string_utc():
    run_of_string(
        "2022-01-01 00:00:00+0000",
        expected=arbitrary_date_in_timezone(timezone=datetime.timezone.utc),
    )


def of_string_minus_offset():
    run_of_string(
        "2022-01-01 00:00:00-0100",
        expected=arbitrary_date_in_timezone(
            timezone=datetime.timezone(offset=datetime.timedelta(hours=-1)),
        ),
    )


def of_string_plus_offset():
    run_of_string(
        "2022-01-01 00:00:00+0100",
        expected=arbitrary_date_in_timezone(
            timezone=datetime.timezone(offset=datetime.timedelta(hours=1)),
        ),
    )


def run_all_of_string():
    of_string_utc()
    of_string_minus_offset()
    of_string_plus_offset()


def run_roundtrip(timezone: datetime.timezone):
    utc_time = arbitrary_date_in_timezone(timezone)
    parsed = UtcTime.of_string(str(utc_time))
    assert parsed == utc_time


def roundtrip_utc():
    run_roundtrip(timezone=datetime.timezone.utc)


def roundtrip_minus_offset():
    run_roundtrip(timezone=datetime.timezone(offset=datetime.timedelta(hours=-1)))


def roundtrip_plus_offset():
    run_roundtrip(timezone=datetime.timezone(offset=datetime.timedelta(hours=1)))


def run_all_roundtrip():
    roundtrip_utc()
    roundtrip_minus_offset()
    roundtrip_plus_offset()


def run_diff_to_nearest_second(*, earlier: UtcTime, later: UtcTime, expected: datetime.timedelta):
    assert later.diff_to_nearest_second(earlier) == expected


def diff_to_nearest_second_same_time():
    utc_time = arbitrary_date_in_timezone(timezone=datetime.timezone.utc)

    run_diff_to_nearest_second(
        earlier=utc_time, later=utc_time, expected=datetime.timedelta(seconds=0)
    )


def diff_to_nearest_second_rounds():
    earlier = arbitrary_date_in_timezone(timezone=datetime.timezone.utc)
    later = UtcTime(earlier.value + datetime.timedelta(seconds=35, milliseconds=700))

    run_diff_to_nearest_second(
        earlier=earlier,
        later=later,
        expected=datetime.timedelta(seconds=36),
    )


def run_comparisons():
    earlier = arbitrary_date_in_timezone(timezone=datetime.timezone.utc)
    later = UtcTime(earlier.value + datetime.timedelta(seconds=35, milliseconds=700))

    assert earlier < later


def run_all_diff_to_nearest_second():
    diff_to_nearest_second_same_time()
    diff_to_nearest_second_rounds()


def run_all():
    run_all_of_string()
    run_all_roundtrip()
    run_all_diff_to_nearest_second()
    run_comparisons()


run_all()
