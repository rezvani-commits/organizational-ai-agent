# -*- coding: utf-8 -*-
"""
reference_normalizer.py

wrapper روی number_normalizer.py: به‌جای فقط استخراج عدد، خودِ متن سؤال رو
substitute می‌کنه تا ارجاعات حروفی به قانون (ماده/بند/تبصره/بخش/فصل) به فرم
عددی تبدیل بشن - چیزی که HybridRetriever._ARTICLE_PATTERN نیاز داره.

مثال:
    normalize_legal_references("ماده دوم قانون مدنی رو بگو")
        -> "ماده 2 قانون مدنی رو بگو"
    normalize_legal_references("طبق ماده ۲ بند بیست و یکم")
        -> "طبق ماده ۲ بند 21"   (فرم رقمی موجود دست‌نخورده می‌مونه)

نحوه استفاده:
    from back.intent.reference_normalizer import normalize_legal_references
"""

from back.intent.number_normalizer import ALL_NUMBER_WORDS, _strip_ordinal_suffix, words_to_number

# دقیقاً همون کلماتی که HybridRetriever._ARTICLE_PATTERN می‌شناسه
_REFERENCE_KEYWORDS = {"ماده", "بند", "تبصره", "بخش", "فصل"}


def _is_number_word(word: str) -> bool:
    stripped = _strip_ordinal_suffix(word)
    return word in ALL_NUMBER_WORDS or stripped in ALL_NUMBER_WORDS


def _collect_word_number_span(words, start_idx: int):
    """از start_idx شروع می‌کنه و کلمات پشت‌سرهمِ عددی/ترتیبی/"و" رو جمع می‌کنه."""
    collected = []
    i = start_idx
    while i < len(words):
        w = words[i]
        if _is_number_word(w) or w == "و":
            collected.append(w)
            i += 1
        else:
            break
    # یه "و" آخر تنها (بدون عدد بعدش) نباید جزو عبارت حساب بشه
    while collected and collected[-1] == "و":
        collected.pop()
        i -= 1
    return collected, i


def normalize_legal_references(text: str) -> str:
    """
    هر رخداد «ماده/بند/تبصره/بخش/فصل + عدد حروفی» رو به «کلمه‌ی کلیدی + عدد رقمی»
    تبدیل می‌کنه. اگه بعد از کلمه‌ی کلیدی از اول هم رقم بود (نه حروفی)، دست‌نخورده
    می‌مونه. کلماتی که هیچ ارجاعی نیستن هم عیناً حفظ می‌شن.
    """
    if not text or not text.strip():
        return text

    words = text.split()
    result = []
    i = 0
    n = len(words)

    while i < n:
        word = words[i]
        cleaned = word.strip("،,.:؛؟?!")

        if cleaned in _REFERENCE_KEYWORDS:
            result.append(word)
            i += 1

            number_words, next_i = _collect_word_number_span(words, i)
            if number_words:
                phrase = " ".join(number_words)
                number = words_to_number(phrase)
                if number is not None:
                    result.append(str(number))
                    i = next_i
                    continue
            continue

        result.append(word)
        i += 1

    return " ".join(result)


if __name__ == "__main__":
    samples = [
        "ماده دوم قانون مدنی رو بگو",
        "طبق ماده ۲ بند بیست و یکم قانون کار",
        "بند پنجم ماده چهار رو توضیح بده",
        "تبصره سوم چی میگه؟",
        "حداقل مزد روزانه چقدره؟",  # نباید هیچ تغییری کنه
    ]
    for s in samples:
        print(f"{s!r} -> {normalize_legal_references(s)!r}")
