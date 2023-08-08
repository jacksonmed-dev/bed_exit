from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD

def display_message(message):
    lcd = LCD()

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

