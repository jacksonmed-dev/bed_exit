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

    def clear_line(self, line_number):
        if line_number == 1:
            self.line1 = ""
        elif line_number == 2:
            self.line2 = ""

    def _scroll_thread(self):
        while not self._stop_event.is_set():
            self._scroll_line(self._line1, self._line2)

    def _scroll_line(self, text1, text2):
        scroll_line1 = len(text1) > 16
        scroll_line2 = len(text2) > 16

        if not scroll_line1:
            lcd.text(text1, 1)
        else:
            lcd.text(" " * 16, 1)  # Clear the line

        if not scroll_line2:
            lcd.text(text2, 2)
        else:
            lcd.text(" " * 16, 2)  # Clear the line

        if scroll_line1 or scroll_line2:
            max_length = max(len(text1), len(text2))
            num_chunks = (max_length - 16) // 16 + 1
            remaining_chars = max_length % 16  # Number of characters to display at the end
            for chunk_num in range(num_chunks):
                chunk_start = chunk_num * 16
                if self._stop_event.is_set():
                    break
                if scroll_line1:
                    lcd.text(text1[chunk_start:chunk_start + 16], 1)
                else:
                    lcd.text(" " * 16, 1)  # Clear the line
                if scroll_line2:
                    lcd.text(text2[chunk_start:chunk_start + 16], 2)
                else:
                    lcd.text(" " * 16, 2)  # Clear the line
                time.sleep(0.1)  # Adjust the sleep duration for scrolling speed
            # Display the remaining characters without scrolling
            if remaining_chars > 0:
                if scroll_line1:
                    lcd.text(text1[max_length - remaining_chars:], 1)
                if scroll_line2:
                    lcd.text(text2[max_length - remaining_chars:], 2)

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
