import calendar
from datetime import datetime, timedelta

import pytest

from core.utils.dates import normalize_date_bound, extract_dates_from_text


def test_normalize_none_start_and_end():
    # None start -> 19000101
    assert normalize_date_bound(None, True) == "19000101"

    # None end -> today
    today = datetime.utcnow().strftime("%Y%m%d")
    assert normalize_date_bound(None, False) == today


def test_normalize_year_and_yyyymm_and_yyyymmdd():
    assert normalize_date_bound(2001, True) == "20010101"
    assert normalize_date_bound(2001, False) == "20011231"

    # YYYYMM
    assert normalize_date_bound(202003, True) == "20200301"
    # March 2020 last day is 31
    assert normalize_date_bound(202003, False) == "20200331"

    # YYYYMMDD unchanged (first 8 digits taken)
    assert normalize_date_bound(20200506, True) == "20200506"


def test_normalize_shorter_and_longer_digit_inputs_and_bounds():
    # 5-digit: treated as year+month
    assert normalize_date_bound("20193", True) == "20190301"

    # short year below MIN_YEAR should raise
    with pytest.raises(ValueError):
        normalize_date_bound("20", True)

    # enforce min year
    with pytest.raises(ValueError):
        normalize_date_bound(1800, True)


def test_extract_full_date_and_month_and_range_and_since():
    # Full date
    d_from, d_to = extract_dates_from_text("Published on 2020-03-05")
    assert d_from == 20200305 and d_to is None

    # Month name
    d_from, d_to = extract_dates_from_text("March 2020")
    assert d_from == 20200301 and d_to is None

    # Range
    d_from, d_to = extract_dates_from_text("from 2015 to 2020")
    assert d_from == 2015 and d_to == 2020

    # Since
    d_from, d_to = extract_dates_from_text("since 2018")
    assert d_from == 2018 and d_to is None


def test_extract_last_n_years_and_last_month_and_quarter():
    # Last N years
    now = datetime.utcnow()
    d_from, d_to = extract_dates_from_text("last 2 years")
    expected_from = now.year - 2 + 1
    assert d_from == expected_from and d_to == now.year

    # Last month -> start is 1st of previous month, end is today
    d_from, d_to = extract_dates_from_text("last month")
    now_dt = datetime.utcnow()
    prev_month = now_dt.month - 1
    prev_year = now_dt.year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    expected_start = int(f"{prev_year:04d}{prev_month:02d}01")
    expected_end = int(now_dt.strftime("%Y%m%d"))
    assert d_from == expected_start and d_to == expected_end

    # Quarter
    d_from, d_to = extract_dates_from_text("Q1 2018")
    assert d_from == 20180101 and d_to == 20180331
