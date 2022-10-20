import random
import threading
import time
from configuration import config

config_massage = config['MASSAGE']
config_paths = config['PATHS']

class Massage(threading.Thread):
    __composition = {
        "head": [i for i in range(0, 1)],
        "shoulders": [i for i in range(1, 2)],
        "back": [i for i in range(3, 4)],
        "butt": [i for i in range(5, 6)],
        "calves": [i for i in range(6, 7)],
        "feet": [i for i in range(7, 8)]
    }
    __massage_type = int(config_massage['TYPE'])
    __massage_status = config_massage.getboolean('STATUS')

    def __init__(self, gpio):
        super(Massage, self).__init__()
        self.lock = threading.Lock()
        self.__gpio = gpio
        return

    def run(self):
        print("Starting Message \n\n\n")
        self.inflate_all()
        print("Check complete... Massage Starting")
        while self.__massage_status:
            self.basic_wave()
            time.sleep(2)
        return

    def set_massage_status(self, value: bool):
        self.lock.acquire()
        self.__massage_status = value
        self.lock.release()

    def check_massage_thread_state(self):
        if not self.__massage_status:
            self.inflate_all()
            return False
        else:
            return True

    def basic_wave(self):
        print("Basic Massage Wave")
        offset = 3
        max_val = self.__gpio.get_num_gpio_pins()
        for i in range(max_val + offset):
            if not self.check_massage_thread_state(): return

            if (i - offset) >= 0:
                print("Setting Relay: {}, State: 1".format(i - offset))
                self.__gpio.set_relay(i - offset, state=1)
            if i < max_val:
                print("Setting Relay: {}, State: 0".format(i))
                self.__gpio.set_relay(i, state=0)
            self.__gpio.change_relay_state()

            time.sleep(1)
        return

    def inflate_all(self):
        max_val = self.__gpio.get_num_gpio_pins() - 1
        for i in range(max_val):
            print("Setting Relay: {}, State: 1".format(i))
            self.__gpio.set_relay(i, state=1)
        self.__gpio.change_relay_state()

    def inflate_all_slowly(self):
        print("Inflating everything Slowly")
        max_val = 20 - 1
        for i in range(1, max_val):
            random_val = random.randint(1, max_val)
            self.__gpio.set_relay(random_val, state=0)
            self.__gpio.change_relay_state()
            time.sleep(0.5)
            self.__gpio.set_relay(random_val, state=1)
            self.__gpio.change_relay_state()
            time.sleep(5)
        return

    def head_inflate(self):
        self.__gpio.set_relays(self.__composition['head'], state=1)
        self.__gpio.change_relay_state()
        return

    def head_deflate(self):
        self.__gpio.set_relays(self.__composition['head'], state=0)
        self.__gpio.change_relay_state()
        return

    def shoulders_inflate(self):
        self.__gpio.set_relays(self.__composition['shoulders'], state=1)
        self.__gpio.change_relay_state()
        return

    def shoulders_deflate(self):
        self.__gpio.set_relays(self.__composition['shoulders'], state=0)
        self.__gpio.change_relay_state()
        return

    def back_inflate(self):
        self.__gpio.set_relays(self.__composition['back'], state=1)
        self.__gpio.change_relay_state()
        return

    def back_deflate(self):
        self.__gpio.set_relays(self.__composition['back'], state=0)
        self.__gpio.change_relay_state()
        return

    def butt_inflate(self):
        self.__gpio.set_relays(self.__composition['butt'], state=1)
        self.__gpio.change_relay_state()
        return

    def butt_deflate(self):
        self.__gpio.set_relays(self.__composition['butt'], state=0)
        self.__gpio.change_relay_state()
        return

    def calves_inflate(self):
        self.__gpio.set_relays(self.__composition['calves'], state=1)
        self.__gpio.change_relay_state()
        return

    def calves_deflate(self):
        self.__gpio.set_relays(self.__composition['calves'], state=0)
        self.__gpio.change_relay_state()
        return

    def feet_inflate(self):
        self.__gpio.set_relays(self.__composition['feet'], state=1)
        self.__gpio.change_relay_state()
        return

    def feet_deflate(self):
        self.__gpio.set_relays(self.__composition['feet'], state=0)
        self.__gpio.change_relay_state()
        return

    def set_massage_type(self, value):
        # Check to see if value corresponds to correct number of massages. Currently, there is one massage
        if value != 1:
            raise ValueError("The massage value cannot be {}. Check how many massages are available".format(value))
        else:
            self.__massage_type = value
