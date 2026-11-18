import pytesseract
from PIL import ImageOps
from pytesseract import Output

from config import (
    BUTTON_SLOTS,
    IMAGE_SCALE,
    MIN_NEW_WORD_LENGTH,
    TESSERACT_CONFIG,
    TESSERACT_PATH,
)
from text_utils import normalize

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


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


def slot_for_word(left, top, width, height):
    center_x = (left + width / 2) / IMAGE_SCALE
    center_y = (top + height / 2) / IMAGE_SCALE

    for slot_name, slot_left, slot_top, slot_right, slot_bottom in BUTTON_SLOTS:
        if slot_left <= center_x < slot_right and slot_top <= center_y < slot_bottom:
            return slot_name

    return None


def read_slot_texts(img):
    data = pytesseract.image_to_data(
        preprocess_image(img),
        lang="eng",
        config=TESSERACT_CONFIG,
        output_type=Output.DICT,
    )
    slot_words = {name: [] for name, *_ in BUTTON_SLOTS}

    for index, raw_word in enumerate(data["text"]):
        word = normalize(raw_word)
        if not word:
            continue

        try:
            confidence = float(data["conf"][index])
        except ValueError:
            confidence = -1

        if confidence < 50:
            continue

        slot = slot_for_word(
            data["left"][index],
            data["top"][index],
            data["width"][index],
            data["height"][index],
        )
        if slot:
            slot_words[slot].append(word)

    texts = []
    for name, *_ in BUTTON_SLOTS:
        text = normalize(" ".join(slot_words[name]))
        if text and len(text) >= MIN_NEW_WORD_LENGTH:
            texts.append(text)

    return texts