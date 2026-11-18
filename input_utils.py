import ctypes
import time
from ctypes import wintypes

from config import LEFT_MOUSE_KEY_CODE, STOP_KEY_CODE


def _key_down(key_code):
    return bool(ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000)


def stop_requested():
    return _key_down(STOP_KEY_CODE)


def wait_for_click():
    last_left_down = _key_down(LEFT_MOUSE_KEY_CODE)

    while True:
        if stop_requested():
            return None

        left_down = _key_down(LEFT_MOUSE_KEY_CODE)
        if left_down and not last_left_down:
            point = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            return point.x, point.y

        last_left_down = left_down
        time.sleep(0.01)