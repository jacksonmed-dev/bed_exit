import time
from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD

lcd = LCD()


def display_message(message):
    def safe_exit(signum, frame):
        exit(1)

    try:
        signal(SIGTERM, safe_exit)
        signal(SIGHUP, safe_exit)

        lcd.text(message, 1)
        lcd.text("", 2)

        pause()

    except KeyboardInterrupt:
        pass

    finally:
        lcd.clear()


def safe_exit(signum, frame):
    exit(1)


def scroll_text(text, line, speed=0.5):
    text = text + " " * 16  # Add padding to the end of the text
    text_length = len(text)

    try:
        signal(SIGTERM, safe_exit)
        signal(SIGHUP, safe_exit)

        while True:
            for i in range(text_length - 16 + 1):
                lcd.text(text[i:i + 16], line)
                time.sleep(speed)


    except KeyboardInterrupt:
        pass

    finally:
        lcd.clear()
