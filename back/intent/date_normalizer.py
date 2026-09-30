import re
from dataclasses import dataclass
from typing import Optional

from back.intent.number_normalizer import (
    normalize_digits,
    words_to_number,
    ALL_NUMBER_WORDS,
    _strip_ordinal_suffix,
)

MONTH_NAMES = {
    "فروردین": 1, "اردیبهشت": 2, "خرداد": 3, "تیر": 4,
    "مرداد": 5, "امرداد": 5, "شهریور": 6,
    "مهر": 7, "آبان": 8, "ابان": 8, "آذر": 9, "اذر": 9,
    "دی": 10, "بهمن": 11, "اسفند": 12,
}


@dataclass
class PersianDate:
    year: int
    month: int
    day: int

    def to_iso(self) -> str:
        """فرمت استاندارد قابل ذخیره/مقایسه: YYYY-MM-DD (تقویم شمسی)."""
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    def __str__(self) -> str:
        return self.to_iso()


def _extract_numeric_date(text: str) -> Optional[PersianDate]:
    normalized = normalize_digits(text)
    m = re.search(r"(\d{3,4})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})", normalized)
    if m:
        year, month, day = (int(g) for g in m.groups())
        return PersianDate(year=year, month=month, day=day)
    return None


def _extract_worded_date(text: str) -> Optional[PersianDate]:
    words = text.split()

    month_index = None
    month_number = None
    for i, w in enumerate(words):
        cleaned = w.strip("،,.")
        if cleaned in MONTH_NAMES:
            month_index = i
            month_number = MONTH_NAMES[cleaned]
            break

    if month_index is None:
        return None

    day_words = words[:month_index]
    day_phrase_words = []
    for w in reversed(day_words):
        stripped = _strip_ordinal_suffix(w)
        if w in ALL_NUMBER_WORDS or stripped in ALL_NUMBER_WORDS or w == "و" or w.isdigit():
            day_phrase_words.insert(0, w)
        else:
            if day_phrase_words:
                break
            continue
    day_phrase = " ".join(day_phrase_words) if day_phrase_words else None

    day_value = None
    if day_phrase:
        normalized_day = normalize_digits(day_phrase)
        if normalized_day.strip().isdigit():
            day_value = int(normalized_day.strip())
        else:
            day_value = words_to_number(day_phrase)

    if day_value is None:
        return None

    year_words = words[month_index + 1:]
    year_phrase_words = []
    for w in year_words:
        cleaned = w.strip("،,.")
        if cleaned == "سال":
            continue
        stripped = _strip_ordinal_suffix(cleaned)
        if cleaned in ALL_NUMBER_WORDS or stripped in ALL_NUMBER_WORDS or cleaned == "و" or cleaned.isdigit() or normalize_digits(cleaned).isdigit():
            year_phrase_words.append(cleaned)
        else:
            if year_phrase_words:
                break
            continue

    year_value = None
    if year_phrase_words:
        year_phrase = " ".join(year_phrase_words)
        normalized_year = normalize_digits(year_phrase)
        if normalized_year.replace(" ", "").isdigit():
            year_value = int(normalized_year.replace(" ", ""))
        else:
            year_value = words_to_number(year_phrase)

    if year_value is None:
        return None

    return PersianDate(year=year_value, month=month_number, day=day_value)


def extract_date(text: str) -> Optional[PersianDate]:
    return _extract_numeric_date(text) or _extract_worded_date(text)


if __name__ == "__main__":
    samples = [
        "تاریخ ۱۴۰۳/۵/۱ رو بگو",
        "تاریخ 1403-05-01",
        "اول مرداد ۱۴۰۳",
        "اول مرداد هزار و چهارصد و سه",
        "پنجم مرداد سال هزار و چهارصد و سه",
        "بیست و یکم شهریور ۱۴۰۲",
    ]
    for s in samples:
        result = extract_date(s)
        print(f"{s!r} -> {result}")
