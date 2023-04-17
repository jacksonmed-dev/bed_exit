# import threading
#
# from src.sensor.tactilus import PressureSensor
#
# if __name__ == "__main__":
#     thread = PressureSensor(file_count=60)
#     thread.start()
import json
import requests
from datetime import datetime
from sseclient import SSEClient
import threading

is_present = True  # set the default value of is_present to True
frame_id = None  # initialize global variable "id" to None
frequency = 18000  # framerate in frames per hour. 5 frames per second


def start_api_sse_client():
    global frame_id  # use the global keyword to access and modify the global variable
    url = "http://10.0.0.1/api/sse"
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
    url = "http://10.0.0.1/api/monitor/sse"
    sse = SSEClient(url)
    for response in sse:
        if response.event == 'body':
            data = response.data.strip()
            present_field = json.loads(data)['present']
            if is_present and not present_field:    # indicates a user was in the bed and exited.
                frames = get_frames_within_window()  # get past 300 frames
                formatted_data = format_sensor_data(frames)  # format data for storage
            is_present = present_field  # set the value of is_present to present_field
            print(is_present)
        if response.event == 'storage':
            data = response.data.strip()
            storage_field = json.loads(data)['used']  # percent of storage used
            if storage_field > 85:
                delete_all_frames()


def set_frequency(frequency):
    url = "http://10.0.0.1/api/frequency"
    headers = {"Content-Type": "application/json"}
    payload = {"frequency": frequency}
    response = requests.put(url, headers=headers, json=payload)

    if response.status_code == 204:
        return True
    else:
        return False  # or raise an exception, depending on your requirements


def delete_all_frames():
    url = "http://10.0.0.1/api/monitor/frames"
    response = requests.delete(url)
    if response.status_code == 204:
        print("All frames deleted successfully.")
    else:
        print("Failed to delete frames. Status code:", response.status_code)


def get_frames_within_window():
    if frame_id is None:
        return None  # or raise an exception, depending on your requirements

    if frame_id < 300:
        before_frame = 0
    else:
        before_frame = frame_id - 300

    after_frame = frame_id

    url = f"http://10.0.0.1/api/monitor/frames?before={before_frame}&after={after_frame}"
    response = requests.get(url)

    if response.status_code == 200:
        frames = response.json()
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
        "frequency": frequency,
        "readings": readings
    }
    json_data = json.dumps(data)
    return json_data


if __name__ == '__main__':
    thread1 = threading.Thread(target=start_api_monitor_sse_client)
    thread1.start()
    thread2 = threading.Thread(target=start_api_sse_client)
    thread2.start()
    print("API SSE Client started on separate threads.")
