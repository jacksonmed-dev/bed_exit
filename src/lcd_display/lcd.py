import threading
import time
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP

# Initialize the LCD
lcd = LCD()


class ScrollingText:
    def __init__(self):
        self._thread = None
        self._line1 = ""
        self._line2 = ""
        self._stop_event = threading.Event()

    def _scroll_thread(self):
        while not self._stop_event.is_set():
            if self._line1 or self._line2:
                self._scroll_line(self._line1, 1)
                self._scroll_line(self._line2, 2)

    def _scroll_line(self, text, line):
        if not text:
            return

        text = text + " " * 16
        text_length = len(text)

        for i in range(text_length - 16 + 1):
            if self._stop_event.is_set():
                break
            lcd.text(text[i:i + 16], line)
            time.sleep(0.1)  # Adjust the sleep duration for scrolling speed

    def set_lines(self, line1, line2):
        self._line1 = line1
        self._line2 = line2
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._scroll_thread)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()


def safe_exit(signum, frame):
    lcd.clear()
    exit(0)


# Set up signal handling
signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)
