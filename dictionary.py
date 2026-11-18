from pathlib import Path

from config import ACTIVE_WORDS_FILE
from input_utils import wait_for_click
from text_utils import normalize


def words_file_path(filename):
    return Path(__file__).parent / filename


def load_words_file(filename):
    path = words_file_path(filename)
    click_targets = {}
    aliases = {}

    if not path.exists():
        path.touch()

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


def save_word_location(word, x, y):
    path = words_file_path(ACTIVE_WORDS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    needs_newline = False
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb") as file:
            file.seek(-1, 2)
            needs_newline = file.read(1) not in (b"\n", b"\r")

    with path.open("a", encoding="utf-8") as file:
        if needs_newline:
            file.write("\n")
        file.write(f"{word} | {x},{y}\n")


def add_word_location(word):
    print(f"Brakuje slowa w slowniku: {word}")
    print("Kliknij myszka lokalizacje tego slowa.")

    click = wait_for_click()
    if click is None:
        return False

    x, y = click
    save_word_location(word, x, y)
    CLICK_TARGETS[word] = [(x, y)]
    ALIASES[word] = (word,)
    NEXT_CLICK_INDEX[word] = 0
    print(f"Dodano do {ACTIVE_WORDS_FILE}: {word} | {x},{y}")
    return True


def next_click_point(target):
    points = CLICK_TARGETS[target]
    index = NEXT_CLICK_INDEX[target]
    NEXT_CLICK_INDEX[target] = (index + 1) % len(points)
    return points[index]


def click_points_for_target(target):
    return [next_click_point(target) for _ in CLICK_TARGETS[target]]