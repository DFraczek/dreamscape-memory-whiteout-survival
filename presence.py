from config import (
    BUTTON_COLOR,
    BUTTON_COLOR_TOLERANCE,
    BUTTON_SLOTS,
    DEBUG_PRESENCE,
    MIN_SLOTS_PRESENT,
    PRESENCE_DOWNSCALE,
    SLOT_MIN_FILL,
)


def _slot_fill(pixels, small_size, left, top, right, bottom):
    br, bg, bb = BUTTON_COLOR
    tol = BUTTON_COLOR_TOLERANCE

    x0, x1 = left // PRESENCE_DOWNSCALE, right // PRESENCE_DOWNSCALE
    y0, y1 = top // PRESENCE_DOWNSCALE, bottom // PRESENCE_DOWNSCALE
    x1, y1 = min(x1, small_size[0]), min(y1, small_size[1])

    matched = 0
    total = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = pixels[x, y]
            total += 1
            if abs(r - br) <= tol and abs(g - bg) <= tol and abs(b - bb) <= tol:
                matched += 1

    return matched / total if total else 0.0


def buttons_present(img):
    small = img.convert("RGB").resize(
        (img.width // PRESENCE_DOWNSCALE, img.height // PRESENCE_DOWNSCALE)
    )
    pixels = small.load()

    fills = [
        _slot_fill(pixels, small.size, left, top, right, bottom)
        for _, left, top, right, bottom in BUTTON_SLOTS
    ]
    present = sum(1 for fill in fills if fill >= SLOT_MIN_FILL)

    if DEBUG_PRESENCE:
        print("Wypelnienie slotow:", [f"{f:.2f}" for f in fills], "->", present)

    return present >= MIN_SLOTS_PRESENT