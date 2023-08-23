import threading
import time
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP

# Initialize the LCD
lcd = LCD()


class ScrollingText:
    def __init__(self):
        self._threads = [None] * 2
        self._lines = ["", ""]
        self._stop_event = threading.Event()

    def _scroll_thread(self, text, line):
        text = text + " " * 16
        text_length = len(text)

        while not self._stop_event.is_set():
            for i in range(text_length - 16 + 1):
                if self._stop_event.is_set():
                    break
                lcd.text(text[i:i + 16], line)
                time.sleep(0.1)  # Adjust the sleep duration for scrolling speed

    def set_lines(self, line1, line2):
        self._lines[0] = line1
        self._lines[1] = line2
        self._stop_event.clear()

        if self._threads[0] is None or not self._threads[0].is_alive():
            self._threads[0] = threading.Thread(target=self._scroll_thread, args=(line1, 1))
            self._threads[0].start()

        if self._threads[1] is None or not self._threads[1].is_alive():
            self._threads[1] = threading.Thread(target=self._scroll_thread, args=(line2, 2))
            self._threads[1].start()

    def stop(self):
        self._stop_event.set()
        for thread in self._threads:
            if thread is not None:
                thread.join()


def safe_exit(signum, frame):
    lcd.clear()
    exit(0)


# Set up signal handling
signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)
