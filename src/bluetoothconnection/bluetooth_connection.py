import pathlib

from queue import Queue
import pandas as pd
from bluetooth import *
import socket
import subprocess
import time
import threading
from os import listdir
from os.path import isfile, join
from configuration import config

config_blue = config['BLUETOOTHCONNECTION']
config_paths = config['PATHS']

def format_data(data, header_string):
    header = bytes(header_string, config_blue['ENCODING'])
    trailer = bytes(config_blue['TRAILER'], config_blue['ENCODING'])
    temp = bytes(data, config_blue['ENCODING'])
    message = header + temp + trailer
    return message


class Bluetooth:
    cmd = config_blue['CMD']

    def __init__(self):
        self._gpio_callbacks = []
        self._bed_status_callbacks = []
        self._bed_status_automatic_callbacks = []
        self._bed_massage_callbacks = []
        self._patient_status_callbacks = []

        self.queue = Queue()
        self.uuid = config_blue['UUID']
        time.sleep(1)

        self.establish_bluetooth_connection()


    def establish_bluetooth_connection(self):
        self.server_sock = BluetoothSocket(RFCOMM)
        self.server_sock.bind(("", PORT_ANY))
        self.server_sock.listen(1)
        self.port = self.server_sock.getsockname()[1]

        advertise_service(self.server_sock, "SampleServer",
                          service_id=self.uuid,
                          service_classes=[self.uuid, SERIAL_PORT_CLASS],
                          profiles=[SERIAL_PORT_PROFILE],
                          #                   protocols = [ OBEX_UUID ]
                          )

        subprocess.check_output(self.cmd, shell=True)
        print("Waiting for connection on RFCOMM channel 1")
        self.client_sock, self.client_info = self.server_sock.accept()
        print("Accepted connection from ", self.client_info)

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

    def receive_data(self):
        # client_sock, client_info = self.server_sock.accept()
        print("Accepted connection from ", self.client_info)
        try:
            while True:
                data = self.client_sock.recv(1024)
                if len(data) == 0: break
                self.switch_command(data)
                print("received [%s]" % data)
        except Exception as e:
            print(e)
            print("Connection Lost... Attempting to reestablish bluetooth connection")
            self.server_sock.close()
            self.client_sock.close()
            self.empty_queue()
            self.establish_bluetooth_connection()

    def enqueue_bluetooth_data(self, data, header_string):
        message = format_data(data, header_string)
        self.queue.put(message)

    def loop_through_queue(self):
        while True:
            if not self.queue.empty():
                self.send_data(self.queue.get())

    def empty_queue(self):
        while not self.queue.empty():
            self.queue.get()

    def send_data(self, message):
        length = int(len(message) / 1024) #should I ad this number in configuration?
        try:
            for i in range(length + 1):
                if i * 1024 > len(message):
                    print("Sending Final: ")
                    print(message[i * 1024:len(message)])
                    print(len(message[i * 1024:len(message)]))
                    self.client_sock.send(message[i * 1024:len(message)])
                    # time.sleep(0.2)
                else:
                    print("Sending: ")
                    print(message[i * 1024:(i + 1) * 1024])
                    print(len(message[i * 1024:(i + 1) * 1024]))
                    self.client_sock.send(message[i * 1024:(i + 1) * 1024])
        except Exception as e:
            print(e)
            self.server_sock.close()
            self.client_sock.close()
            self.empty_queue()
            self.establish_bluetooth_connection()

    def send_dummy_data(self):
        current_path = str(pathlib.Path(__file__).parent.resolve())
        path_to_data = current_path + config_paths['DATA']
        only_files = [f for f in listdir(path_to_data) if isfile(join(path_to_data, f))]
        while True:
            for file in only_files:
                df = pd.read_csv(path_to_data + file)
                self.enqueue_bluetooth_data(df["readings"][0], header_string=config_blue['BED_DATA_RESPONSE'])
                time.sleep(3)

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
        if temp[0] == config_blue['PATIENT_STATUS_HEADER']:
            self._notify_patient_status_observers()
            return

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

    def notify_bed_status_automatic_observers(self):
        # Send callback to set_relay function in gpio.py
        for callback in self._bed_status_automatic_callbacks:
            callback()

    def register_bed_status_automatic(self, callback):
        self._bed_status_automatic_callbacks.append(callback)

    def _notify_patient_status_observers(self):
        for callback in self._patient_status_callbacks:
            callback()

    def register_patient_status_observers(self, callback):
        self._patient_status_callbacks.append(callback)
