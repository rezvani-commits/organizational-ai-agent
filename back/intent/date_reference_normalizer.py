# -*- coding: utf-8 -*-
"""
date_reference_normalizer.py

wrapper روی date_normalizer.py: برخلاف extract_date (که فقط یک PersianDate
برمی‌گردونه)، این فایل خودِ متن سؤال رو substitute می‌کنه - هر عبارت تاریخ
حروفی (روز + نام ماه + سال) رو با فرم عددی "YYYY-MM-DD" جایگزین می‌کنه، که
دقیقاً همون فرمتیه که HybridRetriever._DATE_PATTERN می‌شناسه.

مثال:
    normalize_dates_in_query("اول مرداد هزار و چهارصد و سه چه اتفاقی افتاد؟")
        -> "1403-05-01 چه اتفاقی افتاد؟"
    normalize_dates_in_query("بیست و یکم شهریور ۱۴۰۲ رو بگو")
        -> "1402-06-21 رو بگو"

تاریخ‌های از قبل رقمی-اسلشی (مثل «۱۳۹۳/۱۲/۱۳») دست‌نخورده می‌مونن، چون از
قبل با _DATE_PATTERN مچ می‌شن و نیازی به تغییر ندارن (این فایل فقط دنبال
الگوی «روز + نام ماه [+ سال]» می‌گرده، نه فرمت اسلشی).

نحوه استفاده:
    from back.intent.date_reference_normalizer import normalize_dates_in_query
"""

from back.intent.number_normalizer import (
    ALL_NUMBER_WORDS,
    _strip_ordinal_suffix,
    normalize_digits,
    words_to_number,
)
from back.intent.date_normalizer import MONTH_NAMES


def _is_number_token(word: str) -> bool:
    cleaned = word.strip("،,.")
    stripped = _strip_ordinal_suffix(cleaned)
    return (
        cleaned in ALL_NUMBER_WORDS
        or stripped in ALL_NUMBER_WORDS
        or cleaned == "و"
        or normalize_digits(cleaned).isdigit()
    )


def _phrase_to_number(tokens):
    """لیستی از توکن‌ها (رقمی یا حروفی، بدون 'و' اضافه) رو به عدد تبدیل می‌کنه."""
    cleaned_tokens = [t.strip("،,.") for t in tokens if t.strip("،,.") != "و"]
    if not cleaned_tokens:
        return None
    joined_digits = normalize_digits("".join(cleaned_tokens))
    if joined_digits.isdigit():
        return int(joined_digits)
    return words_to_number(" ".join(tokens))


def normalize_dates_in_query(text: str) -> str:
    """
    الگوی «روز(رقمی/حروفی) + نام ماه + [سال](رقمی/حروفی)» رو پیدا و با فرم
    عددی YYYY-MM-DD جایگزین می‌کنه. اگه روز یا سال پیدا نشه، عبارت دست‌نخورده
    می‌مونه (محافظه‌کارانه - فقط وقتی مطمئنیم جایگزین می‌کنیم).
    """
    if not text or not text.strip():
        return text

    words = text.split()
    n = len(words)
    result = []
    i = 0

    while i < n:
        cleaned = words[i].strip("،,.")

        if cleaned not in MONTH_NAMES:
            result.append(words[i])
            i += 1
            continue

        month_number = MONTH_NAMES[cleaned]

        # --- روز: از انتهای result (کلماتی که تازه اضافه کردیم) به عقب بگرد ---
        day_tokens = []
        j = len(result) - 1
        while j >= 0 and _is_number_token(result[j]):
            day_tokens.insert(0, result[j])
            j -= 1

        if not day_tokens:
            # هیچ عدد روزی قبل از نام ماه نبود -> این یه تاریخ نیست، دست نزن
            result.append(words[i])
            i += 1
            continue

        day_value = _phrase_to_number(day_tokens)
        if day_value is None:
            result.append(words[i])
            i += 1
            continue

        # --- سال: بعد از نام ماه بگرد (با رد کردن کلمه‌ی اختیاری "سال") ---
        k = i + 1
        if k < n and words[k].strip("،,.") == "سال":
            k += 1

        year_tokens = []
        m = k
        while m < n and _is_number_token(words[m]):
            year_tokens.append(words[m])
            m += 1

        if not year_tokens:
            # سال پیدا نشد -> مطمئن نیستیم، دست نزن
            result.append(words[i])
            i += 1
            continue

        year_value = _phrase_to_number(year_tokens)
        if year_value is None:
            result.append(words[i])
            i += 1
            continue

        # موفق: روزِ از قبل اضافه‌شده رو از result حذف کن، نام ماه رو رد کن،
        # تاریخ رو به فرم عددی جایگزین کن، و از بعد سال ادامه بده
        del result[len(result) - len(day_tokens):]
        result.append(f"{year_value:04d}-{month_number:02d}-{day_value:02d}")
        i = m
        continue

    return " ".join(result)


if __name__ == "__main__":
    samples = [
        "اول مرداد هزار و چهارصد و سه چه اتفاقی افتاد؟",
        "بیست و یکم شهریور ۱۴۰۲ رو بگو",
        "پنجم مرداد سال هزار و چهارصد و سه",
        "13 بهمن چی شد",  # سال نداره -> دست‌نخورده می‌مونه
        "مصوب ۱۳۹۳/۱۲/۱۳",  # از قبل رقمی-اسلشی -> دست‌نخورده
        "حداقل مزد روزانه چقدره؟",  # اصلاً تاریخ نیست
    ]
    for s in samples:
        print(f"{s!r} -> {normalize_dates_in_query(s)!r}")
