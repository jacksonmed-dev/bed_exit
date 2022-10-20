import json
import time

import RPi.GPIO as GPIO


class Gpio:
    __rasp_pi_available_gpio = []
    __gpio_pins = {}
    __gpio_status_json = ""

    def __init__(self, inflatable_regions):
        self._observers = []
        GPIO.setmode(GPIO.BCM)
        # GPIO.setmode(GPIO.BOARD)

        self.__rasp_pi_available_gpio = [i for i in range(inflatable_regions)]

        for index in range(inflatable_regions):
            self.__gpio_pins[index] = {"gpio_pin": self.__rasp_pi_available_gpio[index], "state": 1}
        GPIO.cleanup()
        for key, value in self.__gpio_pins.items():
            GPIO.setup(value["gpio_pin"], GPIO.OUT)
            GPIO.output(value["gpio_pin"], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(value["gpio_pin"], GPIO.LOW)
            time.sleep(0.1)

    def set_relay(self, pin, state):
        # enable single pin
        self.__gpio_pins[pin]["state"] = state
        for callback in self._observers:
            callback()

    def set_relays(self, pins, state):
        # enable all pins
        if len(pins) <= 1:
            self.__gpio_pins[pins[0]]["state"] = state
        else:
            for pin in pins:
                self.__gpio_pins[pin]["state"] = state
        for callback in self._observers:
            callback()

    def change_relay_state(self):
        for key, value in self.__gpio_pins.items():
            if value["state"] == 0:
                # Turn off GPIO
                GPIO.output(value["gpio_pin"], GPIO.HIGH)  # Turn off
            elif value["state"] == 1:
                GPIO.output(value["gpio_pin"], GPIO.LOW)  # Turn on
            else:
                print("Error: GPIO pin could not be set, improper array value %d" % value)
        for callback in self._observers:
            callback()

    def get_num_gpio_pins(self):
        return len(self.__rasp_pi_available_gpio)

    def get_gpio_pins(self):
        return self.__gpio_pins

    def register_observer(self, callback):
        self._observers.append(callback)
