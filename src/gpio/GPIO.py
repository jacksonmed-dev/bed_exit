import RPi.GPIO as GPIO
import time

# Set the GPIO mode
GPIO.setmode(GPIO.BCM)


# Define the functions to control the relay
def turn_relay_on(pin):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)


def turn_relay_off(pin):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)


# Call this function to clean up GPIO settings before exiting
def cleanup():
    GPIO.cleanup()
    print("GPIO cleanup completed")
