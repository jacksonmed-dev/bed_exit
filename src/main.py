import json
import os
import threading

from botocore.auth import SigV4Auth
from sseclient import SSEClient

from bluetooth_package import BluetoothService
from kinesis import KinesisClient
from sensor import get_frames_within_window, format_sensor_data, delete_all_frames
from wifi import connect_to_wifi_network


# is_present = False  # set the default value of is_present to True
# is_sensor_present = False
#
# is_timer_enabled = False
# timer_thread = None
#
# frame_id = None  # initialize global variable "id" to None
# sensor_url = os.environ["SENSOR_URL"]


# def start_api_monitor_sse_client(kinesis_client):
#     global is_present, is_sensor_present, is_timer_enabled  # use the global keyword to access and modify the global variable
#     global frame_id
#     url = f"{sensor_url}/api/monitor/sse"
#     sse = SSEClient(url)
#     for response in sse:
#         data = response.data.strip()
#         if response.event == 'body':
#             handle_body_event(data, kinesis_client)
#         if response.event == 'newframe':
#             handle_new_frame_event(data)
#         if response.event == 'storage':
#             handle_storage_event(data)
#
#
# # Function to update the is_patient_present variable
# def update_patient_presence():
#     global is_present, is_sensor_present, is_timer_enabled
#     print(f"Updating pi is_present to {is_sensor_present}")
#     is_present = is_sensor_present
#     is_timer_enabled = False
#
#
# def run_update_patient_presence():
#     global is_timer_enabled, timer_thread
#     print("Starting new timer...")
#     is_timer_enabled = True
#     timer_thread = threading.Timer(60, update_patient_presence)
#     timer_thread.start()
#
#
# def handle_body_event(data, kinesis_client):
#     print("############## BODY EVENT ###############")
#     global is_present, is_sensor_present
#     is_sensor_present = json.loads(data)['present']
#     print(f"sensor patient present:\t{is_sensor_present}")
#     print(f"pi patient present:\t{is_present}")
#
#     if is_timer_enabled and timer_thread is not None:
#         print("Cancelling Timer... Body event detected before timer expired")
#         timer_thread.cancel()
#         run_update_patient_presence()  # Run this function on a separate non blocking thread
#     if is_present and not is_sensor_present and not is_timer_enabled:  # indicates a user was in the bed and exited.
#         print("--- PATIENT EXIT DETECTED ---")
#         run_update_patient_presence()  # Run this function on a separate non blocking thread
#         frames = get_frames_within_window(frame_id)  # get past 300 frames
#         formatted_data = format_sensor_data(frames, is_present, frequency=int(
#             os.environ["SENSOR_FREQUENCY"]))  # format data for storage
#         kinesis_client.put_records(formatted_data)
#     if not is_present and is_sensor_present and not is_timer_enabled:
#         print("--- PATIENT ENTRY DETECTED ---")
#         run_update_patient_presence()
#     if not is_timer_enabled:
#         is_present = is_sensor_present
#     print("\n\n")
#
#
# def handle_new_frame_event(data):
#     global frame_id
#     frame_id = json.loads(data)['id']  # percent of storage used
#
#
# def handle_storage_event(data):
#     print("############## STORAGE EVENT ###############")
#     storage_field = json.loads(data)['used']  # percent of storage used
#     print(f"Storage Used: {storage_field}%")
#     if storage_field > 85:
#         delete_all_frames()
#     print("\n\n")
#
#
# def set_wifi(new_password):
#     print("HELLO I THINK I GOT IT WORKING!!!!!")
#     connect_to_wifi_network(network_ssid="Stanfield Wifi", network_password=new_password, wireless_interface="wlan1")

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
            connect_to_wifi_network(network_ssid="DataPort-BT2-2764103-000107", network_password="boditr@k", wireless_interface="wlan1")

    def start_api_monitor_sse_client(self):
        print("starting the sse client")
        url = f"{self.sensor_url}/api/monitor/sse"
        self.sse_client = SSEClient(url)
        for response in self.sse_client:
            data = response.data.strip()
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
                {"eventType": "bedExit", "sensorId": os.environ["SENSOR_SSID"]})
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
    # service.start()
    service.start_api_monitor_sse_client()
    # disconnect_from_wifi_network(wireless_interface="wlan1")
    # connect_to_wifi_network(
    #     network_ssid=os.environ["SENSOR_SSID"],
    #     network_password=os.environ["SENSOR_PASSWORD"],
    #     wireless_interface=os.environ["WIRELESS_INTERFACE"]
    # )
    # set_frequency(int(os.environ["SENSOR_FREQUENCY"]))
    # start_api_monitor_sse_client(KinesisClient())
