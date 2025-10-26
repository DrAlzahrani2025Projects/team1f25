import calendar
from datetime import datetime

import pytest

from core.utils.dates import normalize_date_bound, extract_dates_from_text


@pytest.mark.parametrize(
    "value,is_start,expected",
    [
        (None, True, "19000101"),
        (None, False, datetime.utcnow().strftime("%Y%m%d")),
        (2001, True, "20010101"),
        (2001, False, "20011231"),
        (202003, True, "20200301"),
        (20200506, True, "20200506"),
        ("20193", True, "20190301"),
    ],
)
def test_normalize_date_bound_common_cases(value, is_start, expected):
    """Common normalization inputs are converted to YYYYMMDD strings.

    This test documents the typical behaviors: None defaults, 4-digit year
    expands to start/end-of-year, YYYYMM becomes first/last day of month,
    and 8-digit-like values are preserved (first 8 digits used).
    """
    res = normalize_date_bound(value, is_start)
    assert res == expected


def test_normalize_date_bound_month_end_computation():
    # verify last-day-of-month is calculated correctly for end-bound
    res = normalize_date_bound(202002, False)
    assert res == "20200229"  # 2020 is leap year


@pytest.mark.parametrize("bad", [1800, "20"])
def test_normalize_date_bound_enforces_min_year(bad):
    """Values that result in a year below MIN_YEAR raise ValueError."""
    with pytest.raises(ValueError):
        normalize_date_bound(bad, True)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Published on 2020-03-05", (20200305, None)),
        ("2020/03/05 was the date", (20200305, None)),
        ("20200305", (20200305, None)),
        ("March 5, 2020", (20200305, None)),
        ("Mar 2020", (20200301, None)),
        ("from 2015 to 2020", (2015, 2020)),
        ("between 2010 and 2015", (2010, 2015)),
        ("2015-2020", (2015, 2020)),
        ("since 2018", (2018, None)),
        ("Q1 2018", (20180101, 20180331)),
        ("no dates here", (None, None)),
        ("I need studies from 1999", (1999, None)),
    ],
)
def test_extract_dates_from_text_examples(text, expected):
    """Basic extraction cases for different date formats and phrases."""
    assert extract_dates_from_text(text) == expected


def test_extract_last_n_years_and_months_and_last_month():
    now = datetime.utcnow()

    # last N years
    d_from, d_to = extract_dates_from_text("last 2 years")
    assert d_to == now.year
    assert d_from == now.year - 2 + 1

    # last N months (relative start should be 1st day of the computed start month)
    d_from_m, d_to_m = extract_dates_from_text("last 3 months")
    assert isinstance(d_from_m, int) and isinstance(d_to_m, int)

    # last month: start is the 1st of previous month, end is today
    d1, d2 = extract_dates_from_text("last month")
    prev_month = now.month - 1
    prev_year = now.year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    expected_start = int(f"{prev_year:04d}{prev_month:02d}01")
    expected_end = int(now.strftime("%Y%m%d"))
    assert d1 == expected_start and d2 == expected_end


def test_normalize_non_leap_year_february():
    """Non-leap year February has 28 days."""
    res = normalize_date_bound(202102, False)
    assert res == "20210228"  # 2021 is not a leap year


@pytest.mark.parametrize(
    "month_text,expected_month",
    [
        ("January 2020", (20200101, None)),
        ("February 2020", (20200201, None)),
        ("April 2020", (20200401, None)),
        ("December 2020", (20201201, None)),
    ],
)
def test_extract_month_names_full_range(month_text, expected_month):
    """All month names parse correctly with full names."""
    assert extract_dates_from_text(month_text) == expected_month


def test_extract_relative_phrases_additional_cases():
    """Additional relative-phrase edge cases."""
    now = datetime.utcnow()

    # last 2 years (already covered, but verify consistency)
    d_from, d_to = extract_dates_from_text("last 2 years")
    assert d_to == now.year
    assert d_from == now.year - 2 + 1

    # last 12 months (one year in months)
    d_from_m, d_to_m = extract_dates_from_text("last 12 months")
    assert isinstance(d_from_m, int) and isinstance(d_to_m, int)
    assert d_to_m == int(now.strftime("%Y%m%d"))


@pytest.mark.parametrize(
    "text",
    [
        "absolutely nothing here",
        "foo bar baz",
    ],
)
def test_extract_no_dates_return_none(text):
    """Strings with no recognizable date patterns return (None, None)."""
    d_from, d_to = extract_dates_from_text(text)
    assert d_from is None and d_to is None

