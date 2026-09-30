from back.intent.number_normalizer import ALL_NUMBER_WORDS, _strip_ordinal_suffix, words_to_number

_REFERENCE_KEYWORDS = {"ماده", "بند", "تبصره", "بخش", "فصل"}


def _is_number_word(word: str) -> bool:
    stripped = _strip_ordinal_suffix(word)
    return word in ALL_NUMBER_WORDS or stripped in ALL_NUMBER_WORDS


def _collect_word_number_span(words, start_idx: int):
    collected = []
    i = start_idx
    while i < len(words):
        w = words[i]
        if _is_number_word(w) or w == "و":
            collected.append(w)
            i += 1
        else:
            break
    while collected and collected[-1] == "و":
        collected.pop()
        i -= 1
    return collected, i


def normalize_legal_references(text: str) -> str:
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
        "حداقل مزد روزانه چقدره؟",
    ]
    for s in samples:
        print(f"{s!r} -> {normalize_legal_references(s)!r}")
