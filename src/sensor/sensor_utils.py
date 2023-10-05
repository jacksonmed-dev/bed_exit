import json
import logging
import os
import uuid
from datetime import datetime

import requests

sensor_url = os.environ["SENSOR_URL"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)


def initialize_default_sensor():
    # Initialize the sensor default values
    logger.info("Initializing Sensor Values")
    set_frequency(int(os.environ["SENSOR_FREQUENCY"]))
    set_rotation_interval(int(os.environ["SENSOR_ROTATION"]))
    # reset_rotation_interval()


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


def set_default_filters():
    url = f"{sensor_url}/api/filters/spot"
    url2 = f"{sensor_url}/api/filters/smooth"
    url3 = f"{sensor_url}/api/filters/noise"

    headers = {"Content-Type": "application/json"}
    payload = False
    response1 = requests.put(url, headers=headers, json=payload)
    response2 = requests.put(url2, headers=headers, json=payload)
    response3 = requests.put(url3, headers=headers, json=payload)

    if response1.status_code == 204 and response2.status_code == 204 and response3.status_code == 204:
        return True
    else:
        return False  # or raise an exception, depending on your requirements


def set_rotation_interval(new_interval):
    url = f"{sensor_url}/api/monitor/attended/interval"
    headers = {"Content-Type": "application/json"}
    payload = new_interval
    response1 = requests.put(url, headers=headers, json=payload)

    if response1.status_code == 204:
        return True
    else:
        return False  # or raise an exception, depending on your requirements


def reset_rotation_interval():
    url = f"{sensor_url}/api/monitor/attended/ok"
    headers = {"Content-Type": "application/json"}
    payload = True
    response1 = requests.put(url, headers=headers, json=payload)

    if response1.status_code == 204:
        return True
    else:
        return False  #


def delete_all_frames():
    url = f"{sensor_url}/api/monitor/frames"
    response = requests.delete(url)
    if response.status_code == 204:
        logger.info("All frames deleted successfully.")
    else:
        logger.error("Failed to delete frames. Status code:", response.status_code)


def get_frames_within_window(frame_id):
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


def check_sensor_connection():
    url = f"{sensor_url}/api/monitor/frames"
    logger.info("check_sensor_connection: checking...")

    try:
        response = requests.delete(url, timeout=5)  # Set a timeout value (e.g., 5 seconds)
        if response.status_code == 204:
            logger.info("Sensor Connection: Valid")
            return True
        else:
            logger.info("Sensor Connection: Invalid")
            return False
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False


def get_attended():
    url = f"{sensor_url}/api/monitor/attended"
    try:
        response = requests.get(url, timeout=5)  # Set a timeout value (e.g., 5 seconds)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False


def get_storage():
    url = f"{sensor_url}/api/monitor/storage"
    try:
        response = requests.get(url, timeout=5)  # Set a timeout value (e.g., 5 seconds)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False


def get_body():
    url = f"{sensor_url}/api/monitor/body"
    try:
        response = requests.get(url, timeout=5)  # Set a timeout value (e.g., 5 seconds)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False

def get_current_frame():
    url = f"{sensor_url}/api/frames"
    try:
        response = requests.get(url, timeout=5)  # Set a timeout value (e.g., 5 seconds)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False

def get_monitor():
    url = f"{sensor_url}/api/monitor"
    try:
        response = requests.get(url, timeout=10)  # Set a timeout value (e.g., 5 seconds)
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error("Error while checking sensor connection:", e)
        return False