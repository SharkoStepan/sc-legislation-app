import re

# Словарь: слово -> замена (или None для автозамены звёздочками)
PROFANITY_WORDS = [
    # мат
    "блять", "блядь", "бляд", "бля",
    "хуй", "хуя", "хуе", "хуи", "хуёв", "хуев",
    "пизда", "пизды", "пиздец", "пизде", "пиздой",
    "ебать", "ебёт", "ебет", "ебал", "еблан", "ёбаный", "ёб", "еб",
    "сука", "суки", "сукой",
    "мудак", "мудаки", "мудила",
    "пидор", "пидорас", "пидр",
    "залупа", "залупой",
    "манда", "мандой",
    "ёбнутый", "ёбнул",
    "блядский", "блядина",
    "выёбываться", "наёбывать",
    "ёбаный", "ёбаная",
    "долбоёб", "долбоеб",
    "шлюха", "шлюхи",
    "ублюдок", "ублюдки",
    "уёбок", "уёбище",
    "пиздюк", "пиздабол",
    "хуесос", "хуёсос",
    "ёб твою мать",
    "иди нахуй", "нахуй", "нахуя",
    "ёб вашу мать",
    "пошёл нахуй",
    # грубые, но не всегда мат
    "урод", "уроды",
    "дебил", "дебилы", "дебильный",
    "идиот", "идиоты",
    "тупица", "тупой", "тупые",
    "придурок", "придурки",
    "козёл", "козла", "козлы",
    "скотина", "скот",
]

# Нормализация: е/ё взаимозаменяемы, разные регистры, некоторые замены букв цифрами
def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace('ё', 'е')
    text = text.replace('0', 'о')
    text = text.replace('3', 'е')
    text = text.replace('@', 'а')
    text = text.replace('4', 'ч')
    return text

def _make_stars(word: str) -> str:
    return '*' * len(word)

def censor_text(text: str) -> tuple[str, bool]:
    """
    Возвращает (censored_text, was_censored).
    was_censored = True если было найдено хоть одно плохое слово.
    """
    was_censored = False
    result = text

    # Сортируем по длине (длинные сначала, чтобы "блядский" не разбивался на "бляд")
    sorted_words = sorted(PROFANITY_WORDS, key=len, reverse=True)

    for bad_word in sorted_words:
        # Нормализуем для поиска, но заменяем в оригинале
        pattern = re.compile(
            re.escape(bad_word).replace('е', '[её]').replace('е', '[её]'),
            re.IGNORECASE
        )
        def replace_match(m):
            nonlocal was_censored
            was_censored = True
            return _make_stars(m.group(0))

        result = pattern.sub(replace_match, result)

    return result, was_censored