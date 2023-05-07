import json
import os
import uuid
from datetime import datetime

import requests

sensor_url = os.environ["SENSOR_URL"]


def set_frequency(new_frequency):
    url = f"{sensor_url}/api/frequency"
    url2 = f"{sensor_url}/api/monitor/storage/frequency"
    headers = {"Content-Type": "application/json"}
    payload = new_frequency
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
        after_frame = frame_id - 300
    before_frame = frame_id

    url = f"{sensor_url}/api/monitor/frames?after={after_frame}&before={before_frame}&exclude=risks"
    response = requests.get(url)

    if response.status_code == 200:
        frames = json.loads(response.text)
        return frames
    else:
        return None  # or raise an exception, depending on your requirements


def format_sensor_data(readings, is_present, frequency):
    global frame_id
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    # data = {
    #     "id": frame_id,
    #     "time": timestamp,
    #     "patient_present": is_present,
    #     "frequency": frequency,
    #     "readings": format_readings(readings)
    # }

    output_array = []
    uid = str(uuid.uuid4())
    for i, obj in enumerate(readings):
        output_obj = {
            "PartitionKey": os.environ["PARTITION_KEY"],
            "Data": json.dumps({
                "id": uid,
                "frame": i,
                "time": timestamp,
                "patient_present": is_present,
                "frames_per_hour": frequency,
                "readings": obj["readings"][0]
            })
        }
        output_array.append(output_obj)
    return output_array


def format_readings(readings):
    output_array = []
    for i, obj in enumerate(readings):
        output_obj = {
            "frame": i,
            "readings": obj["readings"][0]
        }
        output_array.append(output_obj)
    return output_array
