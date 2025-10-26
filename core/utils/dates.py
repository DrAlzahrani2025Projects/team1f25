"""Date normalization and extraction utilities.

This module centralizes date parsing/normalization logic used by the
library client and conversation analyzer.
"""
from __future__ import annotations

from datetime import datetime
import calendar
import re
from typing import Optional, Tuple

MIN_YEAR = 1900


def normalize_date_bound(value: Optional[int | str], is_start: bool) -> Optional[str]:
    """Normalize a date-like value into YYYYMMDD string suitable for queries.

    Args:
        value: None, int or str that may contain digits representing a date.
        is_start: True when normalizing a start bound, False for an end bound.

    Returns:
        A string in YYYYMMDD format or None when input is None and caller
        wants no normalization. (Note: callers may treat None specially.)

    Behavior mirrors previous project utilities:
    - None -> start: '19000101', end: today's YYYYMMDD
    - 4-digit year -> YYYY0101 / YYYY1231
    - 6-digit YYYYMM -> YYYYMM01 / YYYYMM<lastday>
    - 8-digit YYYYMMDD -> used as-is
    - other digit lengths -> try to interpret first 4 as year and rest as month/day
    - enforces MIN_YEAR
    """
    if value is None:
        return "19000101" if is_start else datetime.utcnow().strftime("%Y%m%d")

    s = str(value)
    digits = "".join(ch for ch in s if ch.isdigit())

    if not digits:
        return None

    # If we have at least 8 digits, use first 8
    if len(digits) >= 8:
        ymd = digits[:8]
        year = int(ymd[:4])
        if year < MIN_YEAR:
            raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
        return ymd

    # 4-digit year
    if len(digits) == 4:
        year = int(digits)
        if year < MIN_YEAR:
            raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
        return f"{digits}0101" if is_start else f"{digits}1231"

    # 6-digit YYYYMM
    if len(digits) == 6:
        year = int(digits[:4])
        month = int(digits[4:6])
        if year < MIN_YEAR:
            raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
        month = max(1, min(month, 12))
        if is_start:
            return f"{year:04d}{month:02d}01"
        last = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last:02d}"

    # 5,7 or other >4 digits: first 4 are year, rest month/day where possible
    if len(digits) > 4:
        year = int(digits[:4])
        if year < MIN_YEAR:
            raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
        rest = digits[4:]
        if len(rest) == 1:
            month = int(rest)
            month = max(1, min(month, 12))
            if is_start:
                return f"{year:04d}{month:02d}01"
            last = calendar.monthrange(year, month)[1]
            return f"{year:04d}{month:02d}{last:02d}"
        if len(rest) >= 2:
            month = int(rest[:2])
            month = max(1, min(month, 12))
            if is_start:
                return f"{year:04d}{month:02d}01"
            last = calendar.monthrange(year, month)[1]
            return f"{year:04d}{month:02d}{last:02d}"

    # short year-like (<=4 digits but not caught above)
    if len(digits) <= 4 and digits.isdigit():
        year = int(digits)
        if year < MIN_YEAR:
            raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
        return f"{year:04d}0101" if is_start else f"{year:04d}1231"

    # fallback: pad/truncate to 8
    if len(digits) < 8:
        padded = digits.ljust(8, "0")
    else:
        padded = digits[:8]
    year = int(padded[:4])
    if year < MIN_YEAR:
        raise ValueError(f"Year {year} is before minimum allowed {MIN_YEAR}")
    return padded


def extract_dates_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Heuristic extraction of date_from and date_to from natural text.

    Returns a tuple (date_from, date_to) where values are integers either
    YYYY or YYYYMMDD (or full YYYYMMDD) depending on what was found.
    """
    if not text:
        return None, None

    text_low = text.lower()

    # Range like: from 2015 to 2020, between 2010 and 2015, 2015-2020
    m = re.search(r"from\s+(\d{4})\s+(?:to|-)\s+(\d{4})", text_low)
    if not m:
        m = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", text_low)
    if not m:
        m = re.search(r"(\d{4})\s*[-–]\s*(\d{4})", text_low)
    if m:
        y1, y2 = m.groups()
        return int(y1), int(y2)

    # Full date: YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD
    m = re.search(r"(\d{4})[\-/]?(\d{1,2})[\-/]?(\d{1,2})", text_low)
    if m:
        y, mm, dd = m.groups()
        try:
            return int(f"{int(y):04d}{int(mm):02d}{int(dd):02d}"), None
        except Exception:
            pass

    # Month name formats: 'March 2020', 'Mar 2020', 'March 5, 2020'
    month_names = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    m = re.search(rf"{month_names}\s+(\d{{1,2}}),?\s+(\d{{4}})", text_low)
    if m:
        mon, day, yr = m.groups()
        try:
            try:
                month_idx = datetime.strptime(mon, "%b").month if len(mon) == 3 else datetime.strptime(mon, "%B").month
            except Exception:
                month_idx = datetime.strptime(mon[:3], "%b").month
            return int(f"{int(yr):04d}{int(month_idx):02d}{int(day):02d}"), None
        except Exception:
            pass

    # Month + year (no day)
    m = re.search(rf"{month_names}\s+(\d{{4}})", text_low)
    if m:
        mon, yr = m.groups()
        try:
            month_idx = datetime.strptime(mon[:3], "%b").month
            return int(f"{int(yr):04d}{int(month_idx):02d}01"), None
        except Exception:
            pass

    # Range like: from 2015 to 2020, between 2010 and 2015, 2015-2020
    m = re.search(r"from\s+(\d{4})\s+(?:to|-)\s+(\d{4})", text_low)
    if not m:
        m = re.search(r"between\s+(\d{4})\s+and\s+(\d{4})", text_low)
    if not m:
        m = re.search(r"(\d{4})\s*[-–]\s*(\d{4})", text_low)
    if m:
        y1, y2 = m.groups()
        return int(y1), int(y2)

    # Since 2018
    m = re.search(r"since\s+(\d{4})", text_low)
    if m:
        y = int(m.group(1))
        return y, None

    # Last N years
    m = re.search(r"last\s+(\d{1,2})\s+years", text_low)
    if m:
        n = int(m.group(1))
        now = datetime.utcnow().year
        return now - n + 1, now

    # Last N months or 'last month'
    m = re.search(r"last\s+(\d{1,2})\s+months", text_low)
    if m:
        n = int(m.group(1))
        now_dt = datetime.utcnow()
        start_month = (now_dt.month - n + 1)
        start_year = now_dt.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        start = int(f"{start_year:04d}{start_month:02d}01")
        end = int(now_dt.strftime("%Y%m%d"))
        return start, end

    if re.search(r"last\s+month", text_low):
        now_dt = datetime.utcnow()
        mth = now_dt.month - 1
        yr = now_dt.year
        if mth == 0:
            mth = 12
            yr -= 1
        start = int(f"{yr:04d}{mth:02d}01")
        end = int(now_dt.strftime("%Y%m%d"))
        return start, end

    # Quarter like Q1 2018
    m = re.search(r"q([1-4])\s*(\d{4})", text_low)
    if m:
        q, yr = m.groups()
        q = int(q)
        yr = int(yr)
        quarter_map = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
        start_m, end_m = quarter_map[q]
        start = int(f"{yr:04d}{start_m:02d}01")
        end = int(f"{yr:04d}{end_m:02d}31")
        return start, end

    # Single year mention
    m = re.search(r"\b(19|20)\d{2}\b", text_low)
    if m:
        return int(m.group(0)), None

    return None, None



