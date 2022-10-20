class Gpio:
    __rasp_pi_available_gpio = []
    __gpio_pins = {}

    def __init__(self, inflatable_regions):
        self._observers = []
        self.__rasp_pi_available_gpio = [i for i in range(inflatable_regions)]
        for index in range(inflatable_regions):
            self.__gpio_pins[index] = {"gpio_pin": self.__rasp_pi_available_gpio[index], "state": 1}

    def set_relay(self, pin, state):
        # enable all pins
        self.__gpio_pins[pin]["state"] = state

    def set_relays(self, pins, state):
        # enable all pins
        if len(pins) <= 1:
            self.__gpio_pins[pins[0]]["state"] = state
        else:
            for pin in pins:
                self.__gpio_pins[pin]["state"] = state

    def change_relay_state(self):
        return

    def get_num_gpio_pins(self):
        return len(self.__rasp_pi_available_gpio)

    def get_gpio_pins(self):
        return self.__gpio_pins

    def register_observer(self, callback):
        self._observers.append(callback)
