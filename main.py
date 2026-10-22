import ctypes
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pyautogui
import pytesseract
from PIL import ImageOps

ctypes.windll.user32.SetProcessDPIAware()
pyautogui.PAUSE = 0

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_REGION = (887, 1208, 746, 172)

IMAGE_SCALE = 3
TESSERACT_CONFIG = "--oem 3 --psm 6"
STOP_KEY_CODE = 0x77  # F8
LOG_EVERY_SECONDS = 0.6
CLICK_COOLDOWN_SECONDS = 1
TARGET_CLICK_DELAY_SECONDS = 0.7   #1.0 - slow af
                                    #0.4 - normal
                                    #0.001 - fast af
ACTIVE_WORDS_FILE = "maps/conquering_sword.txt"

def strip_accents(text):
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def normalize(text):
    text = strip_accents(text).lower()
    text = text.replace("|", "l").replace("0", "o").replace("1", "l")
    text = text.replace("vv", "w")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


def load_words_file(filename):
    path = Path(__file__).with_name(filename)
    click_targets = {}
    aliases = {}

    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku slownika: {path}")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            raise ValueError(f"{path.name}:{line_number}: oczekiwano formatu: nazwa | x,y | aliasy")

        name = normalize(parts[0])
        coords = [coord.strip() for coord in parts[1].split(",")]
        if len(coords) != 2:
            raise ValueError(f"{path.name}:{line_number}: wspolrzedne musza miec format x,y")

        x, y = int(coords[0]), int(coords[1])
        click_targets.setdefault(name, []).append((x, y))

        if len(parts) >= 3 and parts[2]:
            aliases[name] = tuple(normalize(alias) for alias in parts[2].split(";") if normalize(alias))
        else:
            aliases[name] = (name,)

    return click_targets, aliases


CLICK_TARGETS, ALIASES = load_words_file(ACTIVE_WORDS_FILE)
NEXT_CLICK_INDEX = {target: 0 for target in CLICK_TARGETS}


def preprocess_image(img):
    gray = ImageOps.grayscale(img)
    enlarged = gray.resize((gray.width * IMAGE_SCALE, gray.height * IMAGE_SCALE))
    contrasted = ImageOps.autocontrast(enlarged)
    return contrasted.point(lambda px: 255 if px > 170 else 0)


def read_text(img):
    return pytesseract.image_to_string(
        preprocess_image(img),
        lang="eng",
        config=TESSERACT_CONFIG,
    )

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


TARGET_THRESHOLDS = {
    "flame": 0.95,
    "flare": 0.95,
    "scroll": 0.96,
    "carpet roll": 0.84,
    "strzykwa": 0.88,
    "skrzynka pocztowa": 0.72,
    "balloons": 0.96,
    "hot air balloon": 0.78,
    "sun": 0.95,
    "sunflower": 0.95,
}

TARGET_SCORE_RESOLVERS = (
    resolve_flame_flare,
    resolve_carpet_roll_scroll,
    resolve_balloons_hot_air_balloon,
    resolve_basket_blanket,
    resolve_sun_sunflower,
)


def threshold_for_target(target):
    if target in TARGET_THRESHOLDS:
        return TARGET_THRESHOLDS[target]
    if len(target) == 1:
        return 1.0
    return 0.74


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


def stop_requested():
    return bool(ctypes.windll.user32.GetAsyncKeyState(STOP_KEY_CODE) & 0x8000)


def next_click_point(target):
    points = CLICK_TARGETS[target]
    index = NEXT_CLICK_INDEX[target]
    NEXT_CLICK_INDEX[target] = (index + 1) % len(points)
    return points[index]


def click_points_for_target(target):
    return [next_click_point(target) for _ in CLICK_TARGETS[target]]

def main():
    print("Start. Masz 5 sekund na przelaczenie na okno gry.")
    print(f"Slownik: {ACTIVE_WORDS_FILE}, hasel: {len(CLICK_TARGETS)}")

    # Rozgrzanie Tesseracta PRZED rozpoczeciem gry
    warmup_img = pyautogui.screenshot(region=OCR_REGION)
    read_text(warmup_img)

    time.sleep(5)

    print("Praca rozpoczeta. Zatrzymanie: F8 albo Ctrl+C.")

    last_log = 0.0
    last_clean_text = None
    last_clicked_at = {}

    while True:
        if stop_requested():
            print("Zatrzymano klawiszem F8.")
            break

        img = pyautogui.screenshot(region=OCR_REGION)
        text = read_text(img)
        found_targets, clean_text = find_targets(text)

        now = time.time()
        if clean_text != last_clean_text or now - last_log >= LOG_EVERY_SECONDS:
            print("OCR:", clean_text)
            print("Wykryte cele:", [(target, f"{score:.2f}") for target, score in found_targets])
            last_clean_text = clean_text
            last_log = now

        if found_targets:
            clicked = set()
            for target, score in found_targets:
                if target in clicked:
                    continue
                if time.time() - last_clicked_at.get(target, 0.0) < CLICK_COOLDOWN_SECONDS:
                    continue

                clicked.add(target)

                for x, y in click_points_for_target(target):
                    print(f"Wykryto: {target} ({score:.2f}) -> klikam {x}, {y}")
                    pyautogui.click(x, y)
                    time.sleep(0.04)

                last_clicked_at[target] = time.time()
                time.sleep(TARGET_CLICK_DELAY_SECONDS)
        else:
            time.sleep(0.05)


if __name__ == "__main__":
    main()
