import ctypes
import re
import time
from pathlib import Path

import pyautogui
import pytesseract
from pytesseract import Output
from PIL import ImageOps


class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


ctypes.windll.user32.SetProcessDPIAware()
pyautogui.PAUSE = 0

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

OCR_REGION = (887, 1208, 746, 172)
IMAGE_SCALE = 3
TESSERACT_CONFIG = "--oem 3 --psm 6"
OUTPUT_FILE = Path("collect_words.txt")
STOP_KEY_CODE = 0x77  # F8
BUTTON_SLOTS = [
    ("gora_lewa", 0, 0, 249, 86),
    ("gora_srodek", 249, 0, 498, 86),
    ("gora_prawa", 498, 0, 746, 86),
    ("dol_lewa", 0, 86, 249, 172),
    ("dol_srodek", 249, 86, 498, 172),
    ("dol_prawa", 498, 86, 746, 172),
]


def preprocess_image(img):
    gray = ImageOps.grayscale(img)
    enlarged = gray.resize((gray.width * IMAGE_SCALE, gray.height * IMAGE_SCALE))
    contrasted = ImageOps.autocontrast(enlarged)
    return contrasted.point(lambda px: 255 if px > 170 else 0)


def read_text_from_image(img):
    return pytesseract.image_to_string(
        preprocess_image(img),
        lang="eng",
        config=TESSERACT_CONFIG,
    ).strip()


def slot_for_word(left, top, width, height):
    center_x = (left + width / 2) / IMAGE_SCALE
    center_y = (top + height / 2) / IMAGE_SCALE

    for slot_name, slot_left, slot_top, slot_right, slot_bottom in BUTTON_SLOTS:
        if slot_left <= center_x < slot_right and slot_top <= center_y < slot_bottom:
            return slot_name

    return None


def clean_text(text):
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", text)
    return " ".join(text.split())


def looks_like_label(text):
    if text.isdigit():
        return True

    letters = sum(char.isalpha() for char in text)
    return letters >= 3


def read_button_texts():
    img = pyautogui.screenshot(region=OCR_REGION)
    data = pytesseract.image_to_data(
        preprocess_image(img),
        lang="eng",
        config=TESSERACT_CONFIG,
        output_type=Output.DICT,
    )
    slot_words = {slot_name: [] for slot_name, *_ in BUTTON_SLOTS}

    for index, raw_word in enumerate(data["text"]):
        word = clean_text(raw_word)
        if not word:
            continue

        try:
            confidence = float(data["conf"][index])
        except ValueError:
            confidence = -1

        if confidence < 50:
            continue

        slot_name = slot_for_word(
            data["left"][index],
            data["top"][index],
            data["width"][index],
            data["height"][index],
        )
        if slot_name:
            slot_words[slot_name].append(word)

    texts = []
    for slot_name, *_ in BUTTON_SLOTS:
        text = clean_text(" ".join(slot_words[slot_name]))
        if text and looks_like_label(text):
            texts.append((slot_name, text))

    return texts


def stop_requested():
    return bool(ctypes.windll.user32.GetAsyncKeyState(STOP_KEY_CODE) & 0x8000)


def wait_for_click():
    user32 = ctypes.windll.user32
    last_left_down = bool(user32.GetAsyncKeyState(0x01) & 0x8000)

    while True:
        if stop_requested():
            return None

        left_down = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
        if left_down and not last_left_down:
            point = Point()
            user32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y

        last_left_down = left_down
        time.sleep(0.01)


def save_entry(text, x, y):
    with OUTPUT_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{text} | {x},{y}\n")


def main():
    print("Start za 3 sekundy. Zatrzymanie: F8 albo Ctrl+C.")
    time.sleep(3)
    saved_texts = set()

    while True:
        if stop_requested():
            print("Zatrzymano klawiszem F8.")
            break

        button_texts = [
            (slot_name, text)
            for slot_name, text in read_button_texts()
            if text not in saved_texts
        ]

        if not button_texts:
            print("Nie wykryto tekstu. Ponawiam...")
            time.sleep(0.3)
            continue

        print("Wykryte pola:", button_texts)

        for slot_name, text in button_texts:
            if stop_requested():
                print("Zatrzymano klawiszem F8.")
                return

            print(f"Wykryto tekst: {text}")
            print("Prosze o klikniecie")

            click = wait_for_click()
            if click is None:
                print("Zatrzymano klawiszem F8.")
                return

            x, y = click
            save_entry(text, x, y)
            saved_texts.add(text)
            print(f"Zapisano: {text} | {x},{y} ({slot_name})")
            time.sleep(0.15)


if __name__ == "__main__":
    main()
