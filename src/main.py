import json
import os
import threading

from botocore.auth import SigV4Auth
from sseclient import SSEClient

from bluetooth_package import BluetoothService
from kinesis import KinesisClient
from sensor import get_frames_within_window, format_sensor_data, delete_all_frames, set_frequency, set_rotation_interval, reset_rotation_interval
from wifi import connect_to_wifi_network


class BedExitMonitor:
    def __init__(self):
        self.is_present = False
        self.is_sensor_present = False
        self.is_timer_enabled = False
        self.timer_thread = None
        self.frame_id = None
        self.sensor_url = os.environ["SENSOR_URL"]

        # Store the SSEClient
        self.sse_client = None

        # Initialize BluetoothService and Kinesis client here
        self.bluetooth_service = BluetoothService(callback=self.ble_controller)
        self.kinesis_client = KinesisClient()  # Replace `KinesisClient` with the actual client initialization code

        # Initialize the sensor default values
        set_frequency(int(os.environ["SENSOR_FREQUENCY"]))
        set_rotation_interval(int(os.environ["SENSOR_ROTATION"]))
        reset_rotation_interval()

    # Example controller function
    def ble_controller(self, parsed_info):
        input_array = parsed_info.split(',')
        if input_array[0] == 'start':
            # Start the monitoring
            print("starting the api monitor")
            self.start_api_monitor_sse_client()
        elif input_array[0] == 'stop':
            # Stop the monitoring
            print("stopping the api")
            self.stop_api_monitor_sse_client()
        elif input_array[0] == "wifi":
            print("initializing sensor wifi connection")
            connect_to_wifi_network(network_ssid="DataPort-BT2-2764103-000107", network_password="boditr@k",
                                    wireless_interface="wlan1")

    def start_api_monitor_sse_client(self):
        print("starting the sse client")
        url = f"{self.sensor_url}/api/monitor/sse"
        self.sse_client = SSEClient(url)
        for response in self.sse_client:
            data = response.data.strip()
            if response.event == "attended":
                self.handle_attended_event(data)
            if response.event == 'body':
                print("############## BODY EVENT ###############")
                self.handle_body_event(data)
            if response.event == 'newframe':
                self.handle_new_frame_event(data)
            if response.event == 'storage':
                self.handle_storage_event(data)

    def stop_api_monitor_sse_client(self):
        if self.sse_client is not None:
            self.sse_client.close()
            self.sse_client = None

    def handle_attended_event(self, data):
        is_ok = json.loads(data)['ok']
        if self.is_present:
            print(data)
            if not is_ok:
                print("Calling backend")
                self.kinesis_client.signed_request_v2(os.environ["EVENT_ENDPOINT"],
                                                      {"eventType": "turnTimerExpire", "sensorId": "s1"})
                reset_rotation_interval()
        else:
            reset_rotation_interval()

    def handle_body_event(self, data):
        print("############## BODY EVENT ###############")
        self.is_sensor_present = json.loads(data)['present']
        print(f"sensor patient present:\t{self.is_sensor_present}")
        print(f"pi patient present:\t{self.is_present}")

        if self.is_timer_enabled and self.timer_thread is not None:
            print("Cancelling Timer... Body event detected before timer expired")
            self.timer_thread.cancel()
            self.run_update_patient_presence()

        if self.is_present and not self.is_sensor_present and not self.is_timer_enabled:
            print("--- PATIENT EXIT DETECTED ---")
            print("---- SENDING EXIT EVENT -----")
            self.kinesis_client.signed_request_v2(os.environ["EVENT_ENDPOINT"],
                                                  {"eventType": "bedExit", "sensorId": "s1"})
            self.run_update_patient_presence()
            frames = get_frames_within_window(self.frame_id)
            formatted_data = format_sensor_data(frames, self.is_present, frequency=int(os.environ["SENSOR_FREQUENCY"]))
            self.kinesis_client.put_records(formatted_data)

        if not self.is_present and self.is_sensor_present and not self.is_timer_enabled:
            print("--- PATIENT ENTRY DETECTED ---")
            self.run_update_patient_presence()

        if not self.is_timer_enabled:
            self.is_present = self.is_sensor_present
        print("\n\n")

    def handle_new_frame_event(self, data):
        self.frame_id = json.loads(data)['id']

    def handle_storage_event(self, data):
        print("############## STORAGE EVENT ###############")
        storage_field = json.loads(data)['used']
        print(f"Storage Used: {storage_field}%")
        if storage_field > 85:
            delete_all_frames()
        print("\n\n")

    def update_patient_presence(self):
        print(f"Updating pi is_present to {self.is_sensor_present}")
        self.is_present = self.is_sensor_present
        self.is_timer_enabled = False

    def run_update_patient_presence(self):
        print("Starting new timer...")
        self.is_timer_enabled = True
        self.timer_thread = threading.Timer(10, self.update_patient_presence)
        self.timer_thread.start()

    def start(self):
        self.bluetooth_service.start()
        # self.start_api_monitor_sse_client()


if __name__ == '__main__':
    service = BedExitMonitor()
    service.start()
    # service.start_api_monitor_sse_client()
    # disconnect_from_wifi_network(wireless_interface="wlan1")
    # connect_to_wifi_network(
    #     network_ssid=os.environ["SENSOR_SSID"],
    #     network_password=os.environ["SENSOR_PASSWORD"],
    #     wireless_interface=os.environ["WIRELESS_INTERFACE"]
    # )
    # start_api_monitor_sse_client(KinesisClient())
