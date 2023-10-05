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
    set_rotation_interval, reset_rotation_interval, check_sensor_connection, initialize_default_sensor, set_default_filters, get_attended, get_body, get_current_frame, get_storage, get_monitor
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

        self.sensor_recovery_in_progress = False

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
        self.lcd_manager.line1 = "Initializing Bluetooth"

        # Start the Bluetooth service in a separate thread
        bluetooth_service = BluetoothService(callback=self.ble_controller)
        self.bluetooth_service_thread = threading.Thread(target=bluetooth_service.start)
        self.bluetooth_service_thread.start()
        time.sleep(2)

        self.lcd_manager.line2 = "Initializing Sensor"

        network_connection = check_internet_connection()

        if network_connection:
            # Start the API Monitor
            # Set the turn timer to default value
            reset_rotation_interval()
            set_default_filters()
            # self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
            # self.api_monitor_sse_client_thread.start()
            # time.sleep(2)

            self.kinesis_client.write_cloudwatch_log(f"Sensor {os.environ['SENSOR_SSID']} Starting..")
            self.lcd_manager.line1 = "Sensor: Connected"
            self.lcd_manager.line2 = "WiFi: Connected"

            self.monitor_thread = threading.Thread(target=self.status_monitor)
            self.monitor_thread.start()
        else:
            self.lcd_manager.line1 = "Connect Wifi In App"
            self.lcd_manager.line2 = "WiFi: Not Connected"

    # def status_monitor(self):
    #     i = 0
    #     while True:
    #         # check sensor connection
    #         if self.sse_client_last_updated_at is not None:
    #             time_since_last_update = (datetime.now() - self.sse_client_last_updated_at).total_seconds()
    #             if time_since_last_update > 20:
    #                 if not self.sensor_recovery_in_progress:
    #                     self.sensor_recovery_in_progress = True
    #                     logger.info("Starting sensor recovery thread")
    #                     self.kinesis_client.write_cloudwatch_log(f"Sensor {os.environ['SENSOR_SSID']} lost connection. Starting recovery thread")
    #                     threading.Thread(target=self.sensor_recovery).start()
    #
    #         # check network connection
    #         is_network_connected = check_internet_connection()
    #         if not is_network_connected:
    #             self.lcd_manager.line2 = "WiFi: Failed"
    #             logger.error("Wifi Connection lost... Attempting to reconnect")
    #
    #         # check bluetooth status
    #         time.sleep(1)
    #         i = i + 1
    #         if i % 10 == 0:
    #             i = 0  # Reset i to 0, not 1
    #             logger.info("Health Check Passed")
    #             self.kinesis_client.write_cloudwatch_log(
    #                 f"Sensor {os.environ['SENSOR_SSID']}: Health Check Passed")

    def status_monitor(self):
        i = 0
        while True:
            # is_sensor_connected = check_sensor_connection()
            # logger.info(f"is_sensor_connected: {is_sensor_connected}")
            attended = get_monitor()
            # body = get_body()
            # current_frame = get_current_frame()
            # storage = get_storage()

            logger.info(f"monitor: {attended}")
            # logger.info(f"body: {body}")
            # logger.info(f"current_frame: {current_frame}")
            # logger.info(f"storage: {storage}")
            # if is_sensor_connected:


            # else:
            #     logger.error(f"Sensor {os.environ['SENSOR_SSID']}: Sensor Connection Lost... Attempting to Reconnect")
            #     self.kinesis_client.write_cloudwatch_log(
            #         f"Sensor {os.environ['SENSOR_SSID']}: Sensor Connection Lost... Attempting to Reconnect")

            time.sleep(1)
            i = i + 1
            if i % 10 == 0:
                i = 0  # Reset i to 0, not 1
                logger.info("Health Check Passed")
                self.kinesis_client.write_cloudwatch_log(
                    f"Sensor {os.environ['SENSOR_SSID']}: Health Check Passed")

    def sensor_recovery(self):
        self.lcd_manager.line1 = "Recovering Sensor Connection"
        is_sensor_connected = check_sensor_connection()
        if is_sensor_connected:
            logger.info("Sensor connection re-established")
            self.kinesis_client.write_cloudwatch_log(
                f"Sensor {os.environ['SENSOR_SSID']} connection reestablished")
            self.lcd_manager.line1 = "Sensor: Connected"
            # This means the sse client stopped working. But the connection still exists. Restart the sse client
            self.sse_client_last_updated_at = datetime.now()
            self.stop_api_monitor_sse_client()
            self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
            self.api_monitor_sse_client_thread.start()
            self.sensor_recovery_in_progress = False
            logger.info("api_monitor_sse_client_thread: non blocking")
        else:
            # cycle the sensor.
            logger.info("Cycling the sensor power")
            self.kinesis_client.write_cloudwatch_log(
                f"Sensor {os.environ['SENSOR_SSID']}: Cycling sensor power")
            turn_relay_on(self.gpio_pin)
            time.sleep(5)
            turn_relay_off(self.gpio_pin)
            # Wait for sensor to connect
            for i in range(10):
                is_sensor_connected = check_sensor_connection()
                if is_sensor_connected:
                    logger.info("Sensor connection re-established")
                    self.kinesis_client.write_cloudwatch_log(
                        f"Sensor {os.environ['SENSOR_SSID']} connection reestablished")
                    self.lcd_manager.line1 = "Sensor: Connected"
                    self.sse_client_last_updated_at = datetime.now()
                    logger.info("Stopping sse thread")
                    self.stop_api_monitor_sse_client()
                    logger.info("Starting new sse thread")
                    self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
                    self.api_monitor_sse_client_thread.start()
                    self.sensor_recovery_in_progress = False
                    break
                time.sleep(2)

    def api_monitor_sse_client(self):
        logger.info("starting the sse client")
        self.kinesis_client.write_cloudwatch_log(
            f"Sensor {os.environ['SENSOR_SSID']}: Starting sse client")
        initialize_default_sensor()
        url = f"{self.sensor_url}/api/monitor/sse"
        self.sse_client = SSEClient(url)

        try:
            # Timer to periodically check the stopping flag
            def check_stopping_flag():
                while not self.api_monitor_sse_client_thread_stop_flag:
                    time.sleep(1)  # Adjust the interval as needed

                # If flag is set, close the SSE client and exit
                logger.info("closing sse client")
                self.kinesis_client.write_cloudwatch_log(
                    f"Sensor {os.environ['SENSOR_SSID']}: Closing sse client")
                raise Exception("Closing the sse client")

            self.api_monitor_sse_client_thread_stop_flag = False
            stopping_flag_timer = threading.Thread(target=check_stopping_flag)
            stopping_flag_timer.start()

            for response in self.sse_client:
                if self.api_monitor_sse_client_thread_stop_flag:
                    logger.info("closing sse client")
                    return
                self.sse_client_last_updated_at = datetime.now()
                data = response.data.strip()
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
            return

    def stop_api_monitor_sse_client(self):
        if self.api_monitor_sse_client_thread is not None and self.api_monitor_sse_client_thread.is_alive():
            logger.info("api_monitor_sse_client_thread_stop_flag: True")
            self.api_monitor_sse_client_thread_stop_flag = True
            logger.info("joined")

        self.api_monitor_sse_client_thread = None

    def handle_attended_event(self, data):
        is_ok = json.loads(data)['ok']
        countdown = json.loads(data)['countdown']
        if self.is_present:
            logger.info(data)
            if not is_ok and countdown == 0:
                logger.info("--- TURN TIMER EXPIRED ---")
                self.kinesis_client.write_cloudwatch_log(
                    f"Sensor {os.environ['SENSOR_SSID']}: Patient Turn Timer Expired")
                self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                      {"eventType": "turnTimerExpire", "sensorId": os.environ["SENSOR_SSID"]})
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
            self.kinesis_client.write_cloudwatch_log(
                f"Sensor {os.environ['SENSOR_SSID']}: Patient Exit Detected")
            self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                  {"eventType": "bedExit", "sensorId": os.environ["SENSOR_SSID"]})
            self.run_update_patient_presence()
            frames = get_frames_within_window(self.frame_id)
            formatted_data = format_sensor_data(frames, self.is_present, frequency=int(os.environ["SENSOR_FREQUENCY"]))
            self.kinesis_client.put_records(formatted_data)

        if not self.is_present and self.is_sensor_present and not self.is_timer_enabled:
            logger.info("--- PATIENT ENTRY DETECTED ---")
            self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + "/event",
                                                  {"eventType": "bedEntry", "sensorId": os.environ["SENSOR_SSID"]})
            self.run_update_patient_presence()

        if not self.is_timer_enabled:
            self.is_present = self.is_sensor_present
        logger.info("\n\n")

    def handle_new_frame_event(self, data):
        self.frame_id = json.loads(data)['id']

    def handle_storage_event(self, data):
        logger.info("############## STORAGE EVENT ###############")
        self.kinesis_client.write_cloudwatch_log(
            f"Sensor {os.environ['SENSOR_SSID']}: Sensor Storage Full. Deleting to make space for new frames")
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
            if len(input_array) >= 4:
                network_ssid, network_password = input_array[1:3]
                logger.info("initializing sensor wifi connection")
                connect_to_wifi_network(network_ssid=network_ssid, network_password=network_password,
                                        wireless_interface="wlan0")
                is_network_connected = check_internet_connection()
                # is_sensor_connected = check_sensor_connection()
                if is_network_connected:
                    self.lcd_manager.line1 = "Sensor: Connected"
                    self.lcd_manager.line2 = "WiFi: Connected"
                    self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + f"/bed/{input_array[3]}",
                                                          {"sensorId": os.environ["SENSOR_SSID"]}, method="PATCH")
                    self.api_monitor_sse_client_thread = threading.Thread(target=self.api_monitor_sse_client)
                    self.api_monitor_sse_client_thread.start()
                    time.sleep(2)

                    self.monitor_thread = threading.Thread(target=self.status_monitor)
                    self.monitor_thread.start()
        elif command == "bed_id":
            if len(input_array) >= 2:
                bed_id = input_array[1]
                self.bed_id = bed_id
                logger.info(f"setting the bed id: {self.bed_id}")
                self.kinesis_client.signed_request_v2(os.environ["JXN_API_URL"] + f"/bed/{self.bed_id}",
                                                      {"sensorId": os.environ["SENSOR_SSID"]}, method="PATCH")


if __name__ == '__main__':
    service = BedExitMonitor()
    service.start()
