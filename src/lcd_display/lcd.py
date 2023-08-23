import threading
import time
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP

# Initialize the LCD
lcd = LCD()




# Define the scrolling function with built-in threading
class ScrollingText:
    def __init__(self, num_lines=2):
        self._num_lines = num_lines
        self._scroll_threads = [None] * num_lines
        self._stop_event = threading.Event()

    def _scroll_thread(self, text, line, speed):
        text = text + " " * 16
        text_length = len(text)

        while not self._stop_event.is_set():
            for i in range(text_length - 16 + 1):
                if self._stop_event.is_set():
                    break
                lcd.text(text[i:i + 16], line)
                time.sleep(speed)

    def start(self, text, line, speed=0.5):
        line -= 1  # Adjust line index to 0-based

        if self._scroll_threads[line] is not None:
            self._stop_event.set()
            self._scroll_threads[line].join()
            self._stop_event.clear()

        self._scroll_threads[line] = threading.Thread(target=self._scroll_thread, args=(text, line, speed))
        self._scroll_threads[line].start()


def safe_exit(signum, frame):
    lcd.clear()
    exit(0)


# Set up signal handling
signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)


