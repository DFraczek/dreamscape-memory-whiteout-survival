import re
import unicodedata


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