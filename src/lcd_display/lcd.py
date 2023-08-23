import threading
import time
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP

# Initialize the LCD
lcd = LCD()




# Define the scrolling function with built-in threading
class ScrollingText:
    def __init__(self):
        self._stop_event = threading.Event()
        self._text = ""
        self._line = 0
        self._speed = 0.5
        self._thread = None

    def _scroll_thread(self):
        text = self._text + " " * 16
        text_length = len(text)

        while not self._stop_event.is_set():
            for i in range(text_length - 16 + 1):
                if self._stop_event.is_set():
                    break
                lcd.text(text[i:i + 16], self._line)
                time.sleep(self._speed)

    def start(self, text, line, speed=0.5):
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join()

        self._text = text
        self._line = line
        self._speed = speed
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._scroll_thread)
        self._thread.start()


def safe_exit(signum, frame):
    lcd.clear()
    exit(0)


# Set up signal handling
signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)


