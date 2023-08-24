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

    @property
    def line1(self):
        return self._line1

    @line1.setter
    def line1(self, value):
        self._line1 = value
        self._restart_thread()

    @property
    def line2(self):
        return self._line2

    @line2.setter
    def line2(self, value):
        self._line2 = value
        self._restart_thread()

    def _scroll_thread(self):
        while not self._stop_event.is_set():
            self._scroll_line(self._line1, self._line2)

    def _scroll_line(self, text1, text2):
        if not text1 and not text2:
            return

        text1 = text1 + " " * 16
        text2 = text2 + " " * 16
        text_length = len(text1)

        for i in range(text_length - 16 + 1):
            if self._stop_event.is_set():
                break
            lcd.text(text1[i:i + 16], 1)
            lcd.text(text2[i:i + 16], 2)
            time.sleep(0.1)  # Adjust the sleep duration for scrolling speed

    # Adjust the sleep duration for scrolling speed

    def _restart_thread(self):
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._scroll_thread)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None


def safe_exit(signum, frame):
    lcd.clear()
    exit(0)


# Set up signal handling
signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)
