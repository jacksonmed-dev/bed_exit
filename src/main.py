import json
import os
import threading
import logging
import time
from datetime import datetime, timedelta

from bluetooth_package import BluetoothService
from kinesis import AwsClient
from sensor import get_frames_within_window, format_sensor_data, delete_all_frames, reset_rotation_interval, \
    check_sensor_connection, initialize_default_sensor, get_monitor, set_default_filters
from lcd_display import ScrollingText
from wifi import connect_to_wifi_network, check_internet_connection
from gpio import turn_relay_off, turn_relay_on, cleanup
from enum import Enum

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


class ConnectionStatus(Enum):
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    NOT_CONNECTED = "not connected"
    DISCONNECTING = "disconnecting"


class ConnectionType(Enum):
    BLUETOOTH = "bluetooth"
    SENSOR = "sensor"
    WIFI = "wifi"


class Events(Enum):
    BED_EXIT = "bedExit"
    BED_ENTRY = "bedEntry"
    TURN_TIMER = "turnTimerExpire"


class BedExitMonitor:
    def __init__(self):
        self.lcd_manager = ScrollingText()
        self.is_present = False
        self.gpio_pin = 4

        # all threads
        self.bluetooth_service_thread = None

        # Health Check Thread
        self.health_check_thread = None

        # Monitor
        self.monitor_thread = None
        self.status_monitor_flag = True

        self.aws_client = AwsClient()  # Replace `KinesisClient` with the actual client initialization code

    def start(self):
        # Start Health Check
        self.health_check_thread = threading.Thread(target=self.health_check)
        self.health_check_thread.start()

        # Cleanup GPIO
        cleanup()
        self.update_hardware_status(ConnectionType.BLUETOOTH, ConnectionStatus.INITIALIZING)

        # Start the Bluetooth service in a separate thread
        bluetooth_service = BluetoothService(callback=self.ble_controller)
        self.bluetooth_service_thread = threading.Thread(target=bluetooth_service.start)
        self.bluetooth_service_thread.start()
        # time.sleep(2)

        self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.INITIALIZING)

        network_connection = check_internet_connection()

        if network_connection:
            self.status_monitor_flag = True
            self.monitor_thread = threading.Thread(target=self.status_monitor)
            self.monitor_thread.start()
        else:
            self.write_logs("Wifi Connection Failed...", write_aws=False)
            self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.CONNECTED)
            self.update_hardware_status(ConnectionType.WIFI, ConnectionStatus.NOT_CONNECTED)

    def health_check(self):
        while True:
            self.write_logs("Health Check Passed")
            time.sleep(300)

    def status_monitor(self):
        reset_rotation_interval()
        set_default_filters()
        delete_all_frames()

        self.write_logs(f"Sensor {os.environ['SENSOR_SSID']} Starting...")
        self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.CONNECTED)
        self.update_hardware_status(ConnectionType.WIFI, ConnectionStatus.CONNECTED)

        sensor_last_received_at = datetime.now()
        previous_monitor_response = {}

        while True:
            if not self.status_monitor_flag:
                return

            monitor = get_monitor()
            if monitor and monitor != previous_monitor_response:
                previous_monitor_response = monitor
                sensor_last_received_at = datetime.now()
                self.handle_turn_timer(monitor['attended']['countdown'])
                self.handle_bed_exit(monitor['body']['present'])
                self.handle_storage(monitor['storage']['used'])

                logger.debug(f"monitor: {monitor}")
                time.sleep(1)
            elif (datetime.now() - sensor_last_received_at) > timedelta(seconds=20):
                is_recovered = False
                while not is_recovered:
                    is_recovered = self.sensor_recovery()

    def handle_bed_exit(self, is_sensor_present):
        if self.is_present and not is_sensor_present:
            self.is_present = is_sensor_present
            self.write_aws_event(Events.BED_EXIT)

        elif not self.is_present and is_sensor_present:
            self.is_present = is_sensor_present
            self.write_aws_event(Events.BED_ENTRY)

    def handle_storage(self, storage):
        if storage > 80:
            delete_all_frames()

    def handle_turn_timer(self, countdown):
        if countdown < 0:
            if self.is_present:
                self.write_aws_event(Events.TURN_TIMER)
                reset_rotation_interval()
            else:
                reset_rotation_interval()

    def sensor_recovery(self):
        self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.INITIALIZING)
        self.write_logs("Cycling the sensor power")

        turn_relay_on(self.gpio_pin)
        time.sleep(5)
        turn_relay_off(self.gpio_pin)

        max_retry = 10
        for i in range(max_retry):
            # Used for Thread Management. Cannot wait for 20 + seconds.
            if not self.status_monitor_flag:
                return

            is_sensor_connected = check_sensor_connection()
            if is_sensor_connected:
                self.write_logs("Sensor connection re-established")
                self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.CONNECTED)
                return True
            else:
                self.write_logs(f"Re-establishing connection failed. Attempt: {i + 1}/{max_retry}")
            time.sleep(2)
        return False

    def write_logs(self, text, write_aws=True):
        logger.info(f"Sensor {os.environ['SENSOR_SSID']}: {text}")
        if write_aws:
            self.aws_client.write_cloudwatch_log(f"Sensor {os.environ['SENSOR_SSID']}: {text}")

    def write_aws_event(self, event):
        self.write_logs(f"Writing Event: {event}")
        self.aws_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                          {"eventType": event,
                                           "sensorId": os.environ["SENSOR_SSID"]})

    def update_hardware_status(self, connection_type, status):
        if connection_type == ConnectionType.SENSOR:
            self.lcd_manager.line1 = f"{connection_type}: {status}"
        elif connection_type == ConnectionType.WIFI:
            self.lcd_manager.line2 = f"{connection_type}: {status}"
        elif connection_type == ConnectionType.BLUETOOTH:
            self.lcd_manager.line1 = f"{connection_type}: {status}"
        else:
            self.lcd_manager.line1 = f"{connection_type}: {status}"

    def ble_controller(self, parsed_info):
        input_array = parsed_info.split(',')
        if not input_array:
            return  # Empty array, nothing to do

        command = input_array[0].lower()

        if command == "wifi":
            if len(input_array) >= 4:
                network_ssid, network_password = input_array[1:3]
                self.write_logs("initializing sensor wifi connection")
                connect_to_wifi_network(network_ssid=network_ssid, network_password=network_password,
                                        wireless_interface="wlan0")
                is_network_connected = check_internet_connection()
                if is_network_connected:
                    self.update_hardware_status(ConnectionType.SENSOR, ConnectionStatus.CONNECTED)
                    self.update_hardware_status(ConnectionType.WIFI, ConnectionStatus.CONNECTED)

                    self.aws_client.signed_request_v2(os.environ["JXN_API_URL"] + f"/bed/{input_array[3]}",
                                                      {"sensorId": os.environ["SENSOR_SSID"]}, method="PATCH")
                    time.sleep(2)

                    self.monitor_thread = threading.Thread(target=self.status_monitor)
                    self.monitor_thread.start()


if __name__ == '__main__':
    service = BedExitMonitor()
    service.start()
