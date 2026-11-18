import ctypes
import time

import pyautogui

from config import (
    ACTIVE_WORDS_FILE,
    AFTER_ADD_WORD_SECONDS,
    BETWEEN_CLICKS_SECONDS,
    CLICK_COOLDOWN_SECONDS,
    IDLE_SLEEP_SECONDS,
    LOG_EVERY_SECONDS,
    OCR_REGION,
    START_DELAY_SECONDS,
    TARGET_CLICK_DELAY_SECONDS,
)
from dictionary import CLICK_TARGETS, add_word_location, click_points_for_target
from input_utils import stop_requested
from matching import find_targets
from ocr import read_slot_texts, read_text
from presence import buttons_present

ctypes.windll.user32.SetProcessDPIAware()
pyautogui.PAUSE = 0


class OcrLogger:
    def __init__(self):
        self.last_log = 0.0
        self.last_clean_text = None

    def log(self, clean_text, found_targets):
        now = time.time()
        if clean_text != self.last_clean_text or now - self.last_log >= LOG_EVERY_SECONDS:
            print("OCR:", clean_text)
            print("Wykryte cele:", [(target, f"{score:.2f}") for target, score in found_targets])
            self.last_clean_text = clean_text
            self.last_log = now


def click_found_targets(found_targets, last_clicked_at):
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
            time.sleep(BETWEEN_CLICKS_SECONDS)

        last_clicked_at[target] = time.time()
        time.sleep(TARGET_CLICK_DELAY_SECONDS)


def find_unknown_words(img):
    unknown = []
    for slot_text in read_slot_texts(img):
        if slot_text not in CLICK_TARGETS and slot_text not in unknown:
            unknown.append(slot_text)
    return unknown


def learn_unknown_words(img):
    unknown = find_unknown_words(img)

    if not unknown:
        time.sleep(IDLE_SLEEP_SECONDS)
        return True

    for word in unknown:
        if not add_word_location(word):
            print("Zatrzymano klawiszem F8.")
            return False
        time.sleep(AFTER_ADD_WORD_SECONDS)

    return True


def main():
    print(f"Start. Masz {START_DELAY_SECONDS} sekund na przelaczenie na okno gry.")
    print(f"Slownik: {ACTIVE_WORDS_FILE}, hasel: {len(CLICK_TARGETS)}")

    read_text(pyautogui.screenshot(region=OCR_REGION))

    time.sleep(START_DELAY_SECONDS)

    print("Praca rozpoczeta. Zatrzymanie: F8 albo Ctrl+C.")

    logger = OcrLogger()
    last_clicked_at = {}

    while True:
        if stop_requested():
            print("Zatrzymano klawiszem F8.")
            break

        img = pyautogui.screenshot(region=OCR_REGION)

        if not buttons_present(img):
            time.sleep(IDLE_SLEEP_SECONDS)
            continue

        found_targets, clean_text = find_targets(read_text(img))
        logger.log(clean_text, found_targets)

        if found_targets:
            click_found_targets(found_targets, last_clicked_at)
        elif clean_text:
            if not learn_unknown_words(img):
                return
        else:
            time.sleep(IDLE_SLEEP_SECONDS)


if __name__ == "__main__":
    main()