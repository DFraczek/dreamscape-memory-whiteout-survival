from difflib import SequenceMatcher

from dictionary import ALIASES, CLICK_TARGETS
from resolvers import TARGET_SCORE_RESOLVERS
from text_utils import normalize

DEFAULT_THRESHOLD = 0.74

TARGET_THRESHOLDS = {
    "flame": 0.95,
    "flare": 0.95,
    "scroll": 0.96,
    "carpet roll": 0.84,
    "balloons": 0.96,
    "hot air balloon": 0.78,
    "sun": 0.95,
    "sunflower": 0.95,
}


def window_scores(clean_text, phrase):
    phrase_words = phrase.split()
    words = clean_text.split()
    size = len(phrase_words)

    if not words or not phrase_words:
        return []

    if len(words) < size:
        return [SequenceMatcher(None, clean_text, phrase).ratio()]

    return [
        SequenceMatcher(None, " ".join(words[index : index + size]), phrase).ratio()
        for index in range(len(words) - size + 1)
    ]


def contains_exact_phrase(clean_text, phrase):
    phrase_words = phrase.split()
    words = clean_text.split()
    size = len(phrase_words)

    if not phrase_words or len(words) < size:
        return False

    return any(words[index : index + size] == phrase_words for index in range(len(words) - size + 1))


def target_score(clean_text, target):
    aliases = ALIASES.get(target, (target,))
    best = 0.0

    for alias in aliases:
        if contains_exact_phrase(clean_text, alias):
            best = max(best, 1.0)
        else:
            if len(alias) == 1:
                continue

            scores = window_scores(clean_text, alias)
            if scores:
                best = max(best, max(scores))

    return best


def threshold_for_target(target):
    if target in TARGET_THRESHOLDS:
        return TARGET_THRESHOLDS[target]
    if len(target) == 1:
        return 1.0
    return DEFAULT_THRESHOLD


def score_for_target(clean_text, target):
    score = target_score(clean_text, target)
    for resolver in TARGET_SCORE_RESOLVERS:
        score = resolver(clean_text, target, score)
    return score


def find_targets(ocr_text):
    clean_text = normalize(ocr_text)
    found = []

    for target in CLICK_TARGETS:
        if target == "zuraw" and "origami" in clean_text:
            continue

        score = score_for_target(clean_text, target)
        if score >= threshold_for_target(target):
            found.append((target, score))

    found.sort(key=lambda item: len(item[0]), reverse=True)
    return found, clean_text