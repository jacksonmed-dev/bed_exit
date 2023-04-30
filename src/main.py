import json
import os

import requests
from datetime import datetime
from sseclient import SSEClient
import threading
from kinesis import KinesisClient
from wifi import connect_to_wifi_network

is_present = True  # set the default value of is_present to True
frame_id = None  # initialize global variable "id" to None
sensor_url = os.environ["SENSOR_URL"]
frequency = int(os.environ["SENSOR_FREQUENCY"])

kinesis_client = KinesisClient()


def start_api_sse_client():
    global frame_id  # use the global keyword to access and modify the global variable
    url = f"{sensor_url}/api/sse"
    sse = SSEClient(url)
    for response in sse:
        data = response.data.strip()
        if data:
            json_data = json.loads(data)
            if 'id' in json_data:
                frame_id = json_data['id']
                print("ID:", frame_id)
            else:
                print("No ID in response.")


def start_api_monitor_sse_client():
    global is_present  # use the global keyword to access and modify the global variable
    global frame_id
    url = f"{sensor_url}/api/monitor/sse"
    sse = SSEClient(url)
    for response in sse:
        print("EVENT: ", response.event)
        if response.event == 'body':
            data = response.data.strip()
            present_field = json.loads(data)['present']
            if is_present and not present_field:  # indicates a user was in the bed and exited.
                frames = get_frames_within_window()  # get past 300 frames
                formatted_data = format_sensor_data(frames)  # format data for storage
                kinesis_client.put_records(formatted_data)
                print(formatted_data)
            is_present = present_field  # set the value of is_present to present_field
            print(is_present)
        if response.event == 'newframe':
            data = response.data.strip()
            frame_id = json.loads(data)['id']  # percent of storage used
        if response.event == 'storage':
            data = response.data.strip()
            storage_field = json.loads(data)['used']  # percent of storage used
            if storage_field > 85:
                delete_all_frames()


def set_frequency(frequency):
    url = f"{sensor_url}/api/frequency"
    url2 = f"{sensor_url}/api/monitor/storage/frequency"
    headers = {"Content-Type": "application/json"}
    payload = frequency
    response1 = requests.put(url, headers=headers, json=payload)
    response2 = requests.put(url2, headers=headers, json=payload)

    if response1.status_code == 204 and response2.status_code == 204:
        return True
    else:
        return False  # or raise an exception, depending on your requirements


def delete_all_frames():
    url = f"{sensor_url}/api/monitor/frames"
    response = requests.delete(url)
    if response.status_code == 204:
        print("All frames deleted successfully.")
    else:
        print("Failed to delete frames. Status code:", response.status_code)


def get_frames_within_window():
    if frame_id is None:
        return None  # or raise an exception, depending on your requirements

    if frame_id < 300:
        after_frame = 0
    else:
        after_frame = frame_id - 2
    before_frame = frame_id

    url = f"{sensor_url}/api/monitor/frames?after={after_frame}&before={before_frame}"
    response = requests.get(url)

    if response.status_code == 200:
        frames = json.loads(response.text)
        return frames
    else:
        return None  # or raise an exception, depending on your requirements


def format_sensor_data(readings):
    global frame_id
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    data = {
        "id": frame_id,
        "time": timestamp,
        "patient_present": is_present,
        "frequency": frequency,
        "readings": format_readings(readings)
    }
    json_data = json.dumps(data)
    return json_data


def format_readings(readings):
    output_array = []
    for i, obj in enumerate(readings):
        output_obj = {
            "frame": i,
            "readings": obj["readings"][0]
        }
        output_array.append(output_obj)
    return output_array


if __name__ == '__main__':
    # connect_to_wifi_network(
    #     network_ssid=os.environ["SENSOR_SSID"],
    #     network_password=os.environ["SENSOR_PASSWORD"],
    #     wireless_interface=os.environ["WIRELESS_INTERFACE"]
    # )
    set_frequency(frequency)
    start_api_monitor_sse_client()
    # thread1 = threading.Thread(target=start_api_monitor_sse_client)
    # thread1.start()
    print("API SSE Client started on separate threads.")
