import json
import os
import threading
import logging
import time
from datetime import datetime

from sseclient import SSEClient
from bluetooth_package import BluetoothService
from kinesis import KinesisClient
from sensor import get_frames_within_window, format_sensor_data, delete_all_frames, set_frequency, \
    set_rotation_interval, reset_rotation_interval, check_sensor_connection, initialize_default_sensor
from lcd_display import ScrollingText
from wifi import connect_to_wifi_network, check_internet_connection
from gpio import turn_relay_off, turn_relay_on, cleanup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


class BedExitMonitor:
    def __init__(self):
        self.lcd_manager = ScrollingText()
        self.bed_id = None
        self.is_present = False
        self.is_sensor_present = False
        self.is_timer_enabled = False
        self.timer_thread = None
        self.frame_id = None
        self.sensor_url = os.environ["SENSOR_URL"]
        self.gpio_pin = 4

        # all threads
        self.bluetooth_service_thread = None

        # SSE Client
        self.api_monitor_sse_client_thread = None
        self.sse_client = None
        self.api_monitor_sse_client_thread_stop_flag = False
        self.sse_client_last_updated_at = datetime.now()

        # Monitor
        self.monitor_thread = None


        self.kinesis_client = KinesisClient()  # Replace `KinesisClient` with the actual client initialization code
        
        
    def start(self):
        # Cleanup GPIP
        cleanup()

        self.lcd_manager.line1("Hello World")
        time.sleep(4)
        self.lcd_manager.line2("2Hello World2")

        # Start the Bluetooth service in a separate thread
        bluetooth_service = BluetoothService(callback=self.ble_controller)
        self.bluetooth_service_thread = threading.Thread(target=bluetooth_service.start)
        self.bluetooth_service_thread.start()

        # Start the API Monitor
        self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
        self.api_monitor_sse_client_thread.start()

        self.monitor_thread = threading.Thread(target=self.status_monitor)
        self.monitor_thread.start()

    def status_monitor(self):
        # self.lcd_manager.set_lines(f"Sensor Connection: {is_sensor_connected}", f"Wifi Connection: {is_network_connected}")
        while True:
            # check sensor connection
            if self.sse_client_last_updated_at is not None:
                time_since_last_update = (datetime.now() - self.sse_client_last_updated_at).total_seconds()
                if time_since_last_update > 20:
                    logger.error("Sensor Connection lost... Attempting to reconnect")
                    threading.Thread(target=self.sensor_recovery).start()

            # check network connection
            is_network_connected = check_internet_connection()
            if not is_network_connected:
                logger.error("Wifi Connection lost... Attempting to reconnect")

            # check bluetooth status
            time.sleep(1)

    def sensor_recovery(self):
        is_sensor_connected = check_sensor_connection()
        if is_sensor_connected:
            # This means the sse client stopped working. But the connection still exists. Restart the sse client
            self.stop_api_monitor_sse_client()
            self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
            self.api_monitor_sse_client_thread.start()
        else:
            # cycle the sensor.
            turn_relay_on(self.gpio_pin)
            time.sleep(5)
            turn_relay_off(self.gpio_pin)
            # Wait for sensor to connect
            is_sensor_connected = check_sensor_connection()
            for i in range(50):
                is_sensor_connected = check_sensor_connection()
                if is_sensor_connected:
                    break
                time.sleep(10)

            # Example controller function

    def api_monitor_sse_client(self):
        if self.sse_client is not None:
            self.stop_api_monitor_sse_client()

        logger.info("starting the sse client")
        initialize_default_sensor()
        url = f"{self.sensor_url}/api/monitor/sse"
        self.sse_client = SSEClient(url)

        # Timer to periodically check the stopping flag
        def check_stopping_flag():
            while not self.api_monitor_sse_client_thread_stop_flag:
                time.sleep(1)  # Adjust the interval as needed

            # If flag is set, close the SSE client and exit
            self.sse_client.close()
            self.sse_client = None

        stopping_flag_timer = threading.Thread(target=check_stopping_flag)
        stopping_flag_timer.start()

        try:
            for response in self.sse_client:
                self.sse_client_last_updated_at = datetime.now()
                data = response.data.strip()
                logger.info(f"Event Received: {response.event}")
                if response.event == "attended":
                    self.handle_attended_event(data)
                if response.event == 'body':
                    self.handle_body_event(data)
                if response.event == 'newframe':
                    self.handle_new_frame_event(data)
                if response.event == 'storage':
                    self.handle_storage_event(data)

        except Exception as e:
            print("Exception in SSEClient loop:", e)

        finally:
            # Clean up and exit the thread
            stopping_flag_timer.join()  # Wait for the flag checking thread to finish
            self.sse_client.close()
            self.sse_client = None

    def stop_api_monitor_sse_client(self):
        if self.sse_client is not None:
            logger.info("Closing the sensor SSE client")
            self.sse_client.close()
            self.sse_client = None

        if self.api_monitor_sse_client_thread is not None and self.api_monitor_sse_client_thread.is_alive():
            self.api_monitor_sse_client_thread_stop_flag = True
            self.api_monitor_sse_client_thread.join()

        self.api_monitor_sse_client_thread = None

    def handle_attended_event(self, data):
        is_ok = json.loads(data)['ok']
        if self.is_present:
            logger.info(data)
            if not is_ok:
                logger.info("Calling backend")
                self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                      {"eventType": "turnTimerExpire", "sensorId": "s1"})
                reset_rotation_interval()
        else:
            reset_rotation_interval()

    def handle_body_event(self, data):
        self.is_sensor_present = json.loads(data)['present']
        logger.info(f"body event: {data}")

        if self.is_timer_enabled and self.timer_thread is not None:
            self.timer_thread.cancel()
            self.run_update_patient_presence()

        if self.is_present and not self.is_sensor_present and not self.is_timer_enabled:
            logger.info("--- PATIENT EXIT DETECTED ---")
            logger.info("---- SENDING EXIT EVENT -----")
            self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                  {"eventType": "bedExit", "sensorId": "s1"})
            self.run_update_patient_presence()
            frames = get_frames_within_window(self.frame_id)
            formatted_data = format_sensor_data(frames, self.is_present, frequency=int(os.environ["SENSOR_FREQUENCY"]))
            self.kinesis_client.put_records(formatted_data)

        if not self.is_present and self.is_sensor_present and not self.is_timer_enabled:
            logger.info("--- PATIENT ENTRY DETECTED ---")
            self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                  {"eventType": "bedEntry", "sensorId": "s1"})
            self.run_update_patient_presence()

        if not self.is_timer_enabled:
            self.is_present = self.is_sensor_present
        logger.info("\n\n")

    def handle_new_frame_event(self, data):
        self.frame_id = json.loads(data)['id']

    def handle_storage_event(self, data):
        logger.info("############## STORAGE EVENT ###############")
        storage_field = json.loads(data)['used']
        logger.info(f"Storage Used: {storage_field}%")
        if storage_field > 85:
            delete_all_frames()
        logger.info("\n\n")

    def update_patient_presence(self):
        logger.info(f"Updating pi is_present to {self.is_sensor_present}")
        self.is_present = self.is_sensor_present
        self.is_timer_enabled = False

    def run_update_patient_presence(self):
        self.is_timer_enabled = True
        self.timer_thread = threading.Timer(10, self.update_patient_presence)
        self.timer_thread.start()

    def ble_controller(self, parsed_info):
        input_array = parsed_info.split(',')

        if not input_array:
            return  # Empty array, nothing to do

        command = input_array[0].lower()
        if command == 'start':
            if len(input_array) >= 1:
                self.api_monitor_sse_client()
        elif command == 'stop':
            if len(input_array) >= 1:
                self.stop_api_monitor_sse_client()
        elif command == "wifi":
            if len(input_array) >= 3:
                network_ssid, network_password = input_array[1:3]
                logger.info("initializing sensor wifi connection")
                connect_to_wifi_network(network_ssid=network_ssid, network_password=network_password,
                                        wireless_interface="wlan0")
                is_network_connected = check_internet_connection()
                is_sensor_connected = check_sensor_connection()
                if is_network_connected and is_sensor_connected:
                    initialize_default_sensor()
                    self.api_monitor_sse_client()
        elif command == "bed_id":
            if len(input_array) >= 2:
                bed_id = input_array[1]
                self.bed_id = bed_id
                logger.info("setting the bed id: ", self.bed_id)
                self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + f"/bed/{self.bed_id}",
                                                      {"sensorId": os.environ["SENSOR_SSID"]}, method="PATCH")



if __name__ == '__main__':
    service = BedExitMonitor()
    service.start()
