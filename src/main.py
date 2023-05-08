import json
import os
import threading

from sseclient import SSEClient
from kinesis import KinesisClient
from sensor import set_frequency, get_frames_within_window, format_sensor_data, delete_all_frames

is_present = False  # set the default value of is_present to True
is_sensor_present = False

is_timer_enabled = False
timer_thread = None

frame_id = None  # initialize global variable "id" to None
sensor_url = os.environ["SENSOR_URL"]


def start_api_monitor_sse_client(kinesis_client):
    global is_present, is_sensor_present, is_timer_enabled  # use the global keyword to access and modify the global variable
    global frame_id
    url = f"{sensor_url}/api/monitor/sse"
    sse = SSEClient(url)
    for response in sse:
        data = response.data.strip()
        if response.event == 'body':
            handle_body_event(data, kinesis_client)
        if response.event == 'newframe':
            handle_new_frame_event(data)
        if response.event == 'storage':
            handle_storage_event(data)


# Function to update the is_patient_present variable
def update_patient_presence():
    global is_present, is_sensor_present, is_timer_enabled
    print(f"Updating pi is_present to {is_sensor_present}")
    is_present = is_sensor_present
    is_timer_enabled = False


def run_update_patient_presence():
    global is_timer_enabled, timer_thread
    print("Starting new timer...")
    is_timer_enabled = True
    timer_thread = threading.Timer(60, update_patient_presence)
    timer_thread.start()


def handle_body_event(data, kinesis_client):
    print("############## BODY EVENT ###############")
    global is_present, is_sensor_present
    is_sensor_present = json.loads(data)['present']
    print(f"sensor patient present:\t{is_sensor_present}")
    print(f"pi patient present:\t{is_present}")

    if is_timer_enabled and timer_thread is not None:
        print("Cancelling Timer... Body event detected before timer expired")
        timer_thread.cancel()
        run_update_patient_presence()  # Run this function on a separate non blocking thread
    if is_present and not is_sensor_present and not is_timer_enabled:  # indicates a user was in the bed and exited.
        print("--- PATIENT EXIT DETECTED ---")
        run_update_patient_presence()  # Run this function on a separate non blocking thread
        frames = get_frames_within_window(frame_id)  # get past 300 frames
        formatted_data = format_sensor_data(frames, is_present, frequency=int(
            os.environ["SENSOR_FREQUENCY"]))  # format data for storage
        kinesis_client.put_records(formatted_data)
    if not is_present and is_sensor_present and not is_timer_enabled:
        print("--- PATIENT ENTRY DETECTED ---")
        run_update_patient_presence()
    if not is_timer_enabled:
        is_present = is_sensor_present
    print("\n\n")


def handle_new_frame_event(data):
    global frame_id
    frame_id = json.loads(data)['id']  # percent of storage used


def handle_storage_event(data):
    print("############## STORAGE EVENT ###############")
    storage_field = json.loads(data)['used']  # percent of storage used
    print(f"Storage Used: {storage_field}%")
    if storage_field > 85:
        delete_all_frames()
    print("\n\n")


if __name__ == '__main__':
    # connect_to_wifi_network(
    #     network_ssid=os.environ["SENSOR_SSID"],
    #     network_password=os.environ["SENSOR_PASSWORD"],
    #     wireless_interface=os.environ["WIRELESS_INTERFACE"]
    # )
    set_frequency(int(os.environ["SENSOR_FREQUENCY"]))
    start_api_monitor_sse_client(KinesisClient())
