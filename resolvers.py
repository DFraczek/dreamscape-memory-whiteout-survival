def resolve_flame_flare(clean_text, target, score):
    words = clean_text.split()

    if target not in ("flame", "flare"):
        return score

    if "flame" in words:
        return 1.0 if target == "flame" else 0.0

    if "flare" in words:
        return 1.0 if target == "flare" else 0.0

    if any(word.startswith("fla") for word in words):
        return 0.0

    return score


def resolve_carpet_roll_scroll(clean_text, target, score):
    words = clean_text.split()

    if target not in ("carpet roll", "scroll"):
        return score

    has_carpet = "carpet" in words
    has_roll = "roll" in words
    has_scroll = "scroll" in words

    if has_scroll:
        return 1.0 if target == "scroll" else 0.0

    if has_carpet and has_roll:
        return 1.0 if target == "carpet roll" else 0.0

    if has_roll and target == "scroll":
        return 0.0

    if has_carpet and target == "carpet roll":
        return max(score, 0.90)

    return score


def resolve_basket_blanket(clean_text, target, score):
    words = clean_text.split()

    if target not in ("basket", "blanket"):
        return score

    if "basket" in words:
        return 1.0 if target == "basket" else 0.0

    if "blanket" in words:
        return 1.0 if target == "blanket" else 0.0

    return score


def resolve_balloons_hot_air_balloon(clean_text, target, score):
    words = clean_text.split()

    if target not in ("balloons", "hot air balloon"):
        return score

    has_hot = "hot" in words
    has_air = "air" in words
    has_balloon = "balloon" in words
    has_balloons = "balloons" in words

    if has_hot and has_air and (has_balloon or has_balloons):
        return 1.0 if target == "hot air balloon" else 0.0

    if has_balloons:
        return 1.0 if target == "balloons" else 0.0

    if has_balloon and target == "balloons":
        return 0.0

    return score


def resolve_sun_sunflower(clean_text, target, score):
    words = clean_text.split()

    if target not in ("sun", "sunflower"):
        return score

    has_sun = "sun" in words
    has_sunflower = "sunflower" in words

    if has_sunflower:
        return 1.0 if target == "sunflower" else 0.0

    if has_sun:
        return 1.0 if target == "sun" else 0.0

    return score


TARGET_SCORE_RESOLVERS = (
    resolve_flame_flare,
    resolve_carpet_roll_scroll,
    resolve_balloons_hot_air_balloon,
    resolve_basket_blanket,
    resolve_sun_sunflower,
)