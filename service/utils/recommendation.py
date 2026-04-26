import re
from pymorphy3 import MorphAnalyzer
from .recommendation_feedback_db import get_feedback_stats

morph = MorphAnalyzer()

STOP_WORDS = {
    "это", "как", "что", "если", "или", "для", "при", "без",
    "после", "перед", "через", "между", "меня", "мне", "она",
    "они", "его", "ее", "их", "был", "была", "были", "есть",
    "нет", "уже", "еще", "весь", "вся", "все", "тут", "там",
    "просто", "только", "очень", "снова", "чтобы"
}

SYNONYMS = {
    "юрист": "адвокат",
    "адвокат": "адвокат",

    "уволить": "увольнение",
    "увольнение": "увольнение",
    "сократить": "сокращение",
    "сокращение": "сокращение",

    "договор": "контракт",
    "контракт": "контракт",
    "трудовой": "труд",
    "работник": "сотрудник",
    "сотрудник": "сотрудник",
    "работодатель": "наниматель",
    "наниматель": "наниматель",
    "зарплата": "заработная_плата",
    "оклад": "заработная_плата",

    "развод": "расторжение_брака",
    "брак": "расторжение_брака",
    "алименты": "алименты",
    "ребенок": "ребенок",
    "деть": "ребенок",

    "наследство": "наследование",
    "завещание": "наследование",

    "жалоба": "обжалование",
    "обжаловать": "обжалование",
    "суд": "судебное_разбирательство",
    "иск": "судебное_разбирательство",

    "аренда": "найм",
    "квартира": "жилье",
    "жилье": "жилье",
    "жильё": "жилье"
}

#нормализация и лемматизация
def normalize_word(word: str) -> str:
    word = word.lower()
    word = re.sub(r"[^\wёЁа-яА-Я-]", "", word)
    if not word:
        return ""

    lemma = morph.parse(word)[0].normal_form

    if lemma in STOP_WORDS:
        return ""

    return SYNONYMS.get(lemma, lemma)

#выделение терминов
def extract_terms(text: str) -> list[str]:
    words = re.findall(r"[а-яА-ЯёЁa-zA-Z0-9_-]+", text.lower())
    result = []

    for w in words:
        norm = normalize_word(w)
        if norm and len(norm) > 2:
            result.append(norm)

    return result

# похожесть
def calculate_similarity(
    current_title: str,
    current_description: str,
    current_messages_text: str,
    other_title: str,
    other_description: str,
    other_messages_text: str,
) -> int:
    current_title_terms = set(extract_terms(current_title))
    current_description_terms = set(extract_terms(current_description))
    current_messages_terms = set(extract_terms(current_messages_text))

    other_title_terms = set(extract_terms(other_title))
    other_description_terms = set(extract_terms(other_description))
    other_messages_terms = set(extract_terms(other_messages_text))

    score = 0

    for term in current_title_terms:
        if term in other_title_terms:
            score += 5
        elif term in other_description_terms:
            score += 3
        elif term in other_messages_terms:
            score += 2

    for term in current_description_terms:
        if term in other_title_terms:
            score += 2
        elif term in other_description_terms:
            score += 1
        elif term in other_messages_terms:
            score += 1

    for term in current_messages_terms:
        if term in other_title_terms:
            score += 1
        elif term in other_description_terms:
            score += 1
        elif term in other_messages_terms:
            score += 1

    return score

# поправка по да/нет
def apply_feedback_adjustment(base_score: float, source_topic_addr: int, recommended_topic_addr: int) -> tuple[float, dict]:
    feedback = get_feedback_stats(source_topic_addr, recommended_topic_addr)
    yes_count = feedback["yes_count"]
    no_count = feedback["no_count"]
    total_count = feedback["total_count"]

    if total_count < 3:
        final_score = base_score
    else:
        final_score = base_score + 0.5 * (yes_count - no_count)

    return final_score, feedback

# оценка пары тем
def score_topic_pair(current_topic: dict, candidate_topic: dict) -> dict:
    current_addr = current_topic.get("addr")
    candidate_addr = candidate_topic.get("addr")

    base_score = calculate_similarity(
        current_topic.get("title", ""),
        current_topic.get("description", ""),
        current_topic.get("messages_text", ""),
        candidate_topic.get("title", ""),
        candidate_topic.get("description", ""),
        candidate_topic.get("messages_text", ""),
    )

    final_score, feedback = apply_feedback_adjustment(
        base_score,
        current_addr,
        candidate_addr
    )

    return {
        "addr": candidate_addr,
        "title": candidate_topic.get("title", ""),
        "author": candidate_topic.get("author", ""),
        "description": candidate_topic.get("description", ""),
        "score": final_score,
        "base_score": base_score,
        "yes_count": feedback["yes_count"],
        "no_count": feedback["no_count"],
        "total_count": feedback["total_count"],
    }

#рекомендации для одной темы
def build_recommendations(current_topic: dict, all_topics: list[dict], limit: int = 5) -> list[dict]:
    scored = []

    current_addr = current_topic.get("addr")

    for topic in all_topics:
        if topic.get("addr") == current_addr:
            continue

        result = score_topic_pair(current_topic, topic)

        if result["score"] >= 3:
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]

# персональная лента
def build_personalized_recommendations(viewed_topics: list[dict], all_topics: list[dict], limit: int = 10) -> list[dict]:
    viewed_ids = {topic["addr"] for topic in viewed_topics}
    aggregated = {}

    for index, viewed_topic in enumerate(viewed_topics):
        recency_weight = max(0.7, 1.0 - index * 0.1)

        for candidate in all_topics:
            candidate_addr = candidate.get("addr")

            if candidate_addr in viewed_ids:
                continue

            result = score_topic_pair(viewed_topic, candidate)

            if result["score"] < 3:
                continue

            if candidate_addr not in aggregated:
                aggregated[candidate_addr] = {
                    "addr": candidate_addr,
                    "title": candidate.get("title", ""),
                    "author": candidate.get("author", ""),
                    "description": candidate.get("description", ""),
                    "tags": candidate.get("tags", []),
                    "primary_tag": candidate.get("primary_tag"),
                    "tag_keys": candidate.get("tag_keys", []),
                    "score": 0.0,
                    "signals": 0
                }

            aggregated[candidate_addr]["score"] += result["score"] * recency_weight
            aggregated[candidate_addr]["signals"] += 1

    personalized = list(aggregated.values())

    for item in personalized:
        if item["signals"] > 1:
            item["score"] += 0.75 * (item["signals"] - 1)

    personalized.sort(key=lambda x: x["score"], reverse=True)
    return personalized[:limit]

# поиск по форуму. Сравнение запроса с title, description и messages_text всех тем.
def search_topics_by_semantics(query: str, all_topics: list[dict], limit: int = 30) -> list[dict]:
    """
    Семантический 
    Сравнивает пользовательский запрос с title, description и messages_text всех тем.
    """
    query = (query or "").strip()
    if not query:
        return []

    query_topic = {
        "addr": -1,
        "title": query,
        "description": "",
        "messages_text": ""
    }

    scored = []

    for topic in all_topics:
        result = score_topic_pair(query_topic, topic)

        if result["base_score"] >= 3:
            scored.append({
                "addr": topic.get("addr"),
                "title": topic.get("title", ""),
                "author": topic.get("author", ""),
                "description": topic.get("description", ""),
                "score": result["base_score"]
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]