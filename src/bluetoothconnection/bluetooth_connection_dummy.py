import pathlib
import threading
import time
from os import listdir
from os.path import isfile, join
import pandas as pd
from queue import Queue
from configuration import config

config_blue = config['BLUETOOTHCONNECTION']
config_paths = config['PATHS']


class Bluetooth:

    def __init__(self):
        self.queue = Queue()
        self._gpio_callbacks = []
        self._bed_status_automatic_callbacks = []
        self._bed_status_callbacks = []
        self._bed_massage_callbacks = []
        self._patient_status_callbacks = []

    def run(self, send_dummy_data):
        thread1 = threading.Thread(target=self.receive_data)
        thread2 = threading.Thread(target=self.loop_through_queue)
        if send_dummy_data:
            thread3 = threading.Thread(target=self.send_dummy_data)
            thread1.start()
            thread2.start()
            thread3.start()
        else:
            thread1.start()
            thread2.start()

    def enqueue_bluetooth_data(self, data, header_string):
        message = self.format_data(data, header_string)
        self.queue.put(message)

    def loop_through_queue(self):
        while True:
            if not self.queue.empty():
                self.send_data(self.queue.get())

    def format_data(self, data, header_string):
        header = bytes(header_string, config_blue['ENCODING'])
        trailer = bytes(config_blue['TRAILER'], config_blue['ENCODING'])
        temp = bytes(data, config_blue['ENCODING'])
        message = header + temp + trailer
        return message

    def send_data(self, message):
        print("send_data function called")
        print("Data sent: ")
        length = int(len(message) / 1024)

        for i in range(length + 1):
            if i == range(len(message)):
                print(message[i * 1024:len(message)])
                print(len(message[i * 1024:len(message)]))
            else:
                print(message[i * 1024:(i + 1) * 1024])
                print(len(message[i * 1024:(i + 1) * 1024]))

    def send_dummy_data(self):
        current_path = str(pathlib.Path(__file__).parent.resolve())
        path_to_data = current_path + config_paths['DATA']
        only_files = [f for f in listdir(path_to_data) if isfile(join(path_to_data, f))]
        while True:
            for file in only_files:
                df = pd.read_csv(path_to_data + file)
                self.send_data(df["readings"][0], header_string="!")
                time.sleep(5)

    def receive_data(self):
        print("Accepted connection from ", "Python Test")

    # Add error checking when receiving the data
    def switch_command(self, data):
        temp = data.decode(config_blue['ENCODING'])
        if len(temp) == 0: return
        if temp[0] == config_blue['INFLATABLE_REGION_HEADER']:
            pin = int(temp[1])
            state = int(temp[2])
            self._notify_gpio_observers(pin, state)
            return
        if temp[0] == config_blue['MASSAGE_HEADER']:
            value = int(temp[1])
            self._notify_bed_massage(value)
            # setup massage
            return
        if temp[0] == config_blue['BED_DATA_RESPONSE']:
            self._notify_bed_status_observers()  # send the bed json message back
            return
        if temp[0] == config_blue['BED_DATA_RESPONSE_AUTOMATIC']:
            self.notify_bed_status_automatic_observers()  # send the bed json message back
            return

    def _notify_gpio_observers(self, new_value, state):
        # Send callback to set_relay function in gpio.py
        for callback in self._gpio_callbacks:
            callback(new_value, state)

    def register_gpio_callback(self, callback):
        self._gpio_callbacks.append(callback)

    def _notify_bed_massage(self, value):
        for callback in self._bed_massage_callbacks:
            callback(value)

    def register_bed_massage_callback(self, callback):
        self._bed_massage_callbacks.append(callback)

    def _notify_bed_status_observers(self):
        for callback in self._bed_status_callbacks:
            callback()

    def register_bed_status_callback(self, callback):
        self._bed_status_callbacks.append(callback)

    def _notify_gpio_observers(self, new_value, state):
        # Send callback to set_relay function in gpio.py
        for callback in self._gpio_callbacks:
            callback(new_value, state)

    def register_gpio_callback(self, callback):
        self._gpio_callbacks.append(callback)

    def _notify_patient_status_observers(self):
        for callback in self._patient_status_callbacks:
            callback()

    def register_patient_status_observers(self, callback):
        self._patient_status_callbacks.append(callback)

    def register_bed_status_automatic(self, callback):
        self._bed_status_automatic_callbacks.append(callback)
