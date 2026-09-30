import re

# ---------------------------------------------------------------------------
# ۱) تبدیل ارقام فارسی/عربی به ارقام لاتین
# ---------------------------------------------------------------------------

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_LATIN_DIGITS = "0123456789"

_DIGIT_TRANSLATION = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _LATIN_DIGITS + _LATIN_DIGITS,
)


def normalize_digits(text: str) -> str:
    return text.translate(_DIGIT_TRANSLATION)


# ---------------------------------------------------------------------------
# ۲) دیکشنری اعداد حروفی (اصلی) فارسی
# ---------------------------------------------------------------------------

UNITS = {
    "صفر": 0, "یک": 1, "یه": 1, "دو": 2, "سه": 3, "چهار": 4, "پنج": 5,
    "شش": 6, "هفت": 7, "هشت": 8, "نه": 9,
}

TEENS = {
    "ده": 10, "یازده": 11, "دوازده": 12, "سیزده": 13, "چهارده": 14,
    "پانزده": 15, "شانزده": 16, "هفده": 17, "هجده": 18, "نوزده": 19,
}

TENS = {
    "بیست": 20, "سی": 30, "چهل": 40, "پنجاه": 50,
    "شصت": 60, "هفتاد": 70, "هشتاد": 80, "نود": 90,
}

HUNDREDS = {
    "صد": 100, "یکصد": 100, "دویست": 200, "سیصد": 300, "چهارصد": 400,
    "پانصد": 500, "ششصد": 600, "هفتصد": 700, "هشتصد": 800, "نهصد": 900,
}

SCALES = {
    "هزار": 1000,
    "میلیون": 1_000_000,
}

# ---------------------------------------------------------------------------
# ۳) دیکشنری اعداد ترتیبی (اول، دوم، سوم، ...)
#    این‌ها معمولاً برای "ماده‌ی دوم" یا "روز پنجم" استفاده می‌شن
# ---------------------------------------------------------------------------

ORDINALS = {
    "اول": 1, "یکم": 1, "دوم": 2, "سوم": 3, "چهارم": 4, "پنجم": 5,
    "ششم": 6, "هفتم": 7, "هشتم": 8, "نهم": 9, "دهم": 10,
    "یازدهم": 11, "دوازدهم": 12, "سیزدهم": 13, "چهاردهم": 14,
    "پانزدهم": 15, "شانزدهم": 16, "هفدهم": 17, "هجدهم": 18, "نوزدهم": 19,
    "بیستم": 20, "سی‌ام": 30, "سی ام": 30, "چهلم": 40, "پنجاهم": 50,
    "شصتم": 60, "هفتادم": 70, "هشتادم": 80, "نودم": 90, "صدم": 100,
}

ALL_NUMBER_WORDS = (
    set(UNITS) | set(TEENS) | set(TENS) | set(HUNDREDS)
    | set(SCALES) | set(ORDINALS)
)


def _strip_ordinal_suffix(token: str) -> str:
    for suffix in ("‌ام", " ام", "ام", "م"):
        if token.endswith(suffix):
            base = token[: -len(suffix)]
            if base in UNITS or base in TEENS or base in TENS or base in HUNDREDS:
                return base
    return token


def words_to_number(text: str):
    text = text.strip()
    if not text:
        return None

    if text in ORDINALS:
        return ORDINALS[text]

    tokens = [t for t in text.split() if t != "و"]

    total = 0
    current_group = 0
    matched_anything = False

    for raw_token in tokens:
        token = _strip_ordinal_suffix(raw_token)

        if token in ORDINALS and len(tokens) == 1:
            return ORDINALS[token]

        if token in UNITS:
            current_group += UNITS[token]
            matched_anything = True
        elif token in TEENS:
            current_group += TEENS[token]
            matched_anything = True
        elif token in TENS:
            current_group += TENS[token]
            matched_anything = True
        elif token in HUNDREDS:
            current_group += HUNDREDS[token]
            matched_anything = True
        elif token in SCALES:
            scale = SCALES[token]
            if current_group == 0:
                current_group = 1
            total += current_group * scale
            current_group = 0
            matched_anything = True
        else:
            # کلمه ناشناخته - نادیده گرفته می‌شه (مثلاً "ماده" یا "قانون")
            continue

    total += current_group

    return total if matched_anything else None


def extract_number(text: str):
    normalized = normalize_digits(text)

    digit_match = re.search(r"\d+", normalized)
    if digit_match:
        return int(digit_match.group())

    # دنبال توالی کلمات عددی حروفی بگرد
    words = text.split()
    number_word_indices = [
        i for i, w in enumerate(words)
        if _strip_ordinal_suffix(w) in ALL_NUMBER_WORDS or w in ALL_NUMBER_WORDS
    ]
    if not number_word_indices:
        return None

    start, end = number_word_indices[0], number_word_indices[-1]
    phrase = " ".join(words[start:end + 1])
    return words_to_number(phrase)


def extract_article_number(text: str):
    normalized = normalize_digits(text)

    # حالت رقمی: "ماده" + فاصله اختیاری + عدد
    m = re.search(r"ماده\s*[\-:]?\s*(\d+)", normalized)
    if m:
        return int(m.group(1))

    # حالت حروفی: کلمات بعد از "ماده" رو تا برخورد با کلمه غیرعددی بردار
    m = re.search(r"ماده\s+(.+)", text)
    if not m:
        return None

    rest_words = m.group(1).split()
    number_words = []
    for w in rest_words:
        stripped = _strip_ordinal_suffix(w)
        if w in ALL_NUMBER_WORDS or stripped in ALL_NUMBER_WORDS or w == "و":
            number_words.append(w)
        else:
            break

    if not number_words:
        return None

    phrase = " ".join(number_words)
    return words_to_number(phrase)


if __name__ == "__main__":
    # تست سریع دستی
    samples = [
        "ماده ۲ قانون مدنی رو بگو",
        "ماده دوم قانون مدنی رو بگو",
        "ماده 15 رو بخون",
        "ماده پانزدهم چی میگه",
        "طبق ماده بیست و یکم قانون کار",
    ]
    for s in samples:
        print(f"{s!r} -> {extract_article_number(s)}")
