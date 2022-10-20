import json
import threading
from datetime import timedelta
import pandas as pd
from configuration import config, is_raspberry_pi

if is_raspberry_pi:
    from bluetoothconnection.bluetooth_connection import Bluetooth as Bluetooth
else:
    from bluetoothconnection.bluetooth_connection_dummy import Bluetooth as Bluetooth

config_bluetooth = config['BLUETOOTHCONNECTION']


class Patient(object):
    __body_stats_df = pd.DataFrame(0, index=['head', 'shoulders', 'back', 'butt', 'calves', 'feet'],
                                   columns=['time', 'max_pressure'])
    __body = {
        "first_name": " Ben",
        "last_name": "Dover",
        "age": 36,
        "height": 72,
        "weight": 190
    }

    __patient_history = {
        "gender": 'male',
        "BMI": 19,
        "ulcer_history": ['arm', 'leg'],
        "ICU_days": 5,
        "temperature": 101.2,
        "diabetes": 'type_1',
        "systolic_blood_pressure": 125,
        "diastolic_blood_pressure": 77
    }

    __patient_nutrition = {

    }

    def __init__(self, bluetooth: Bluetooth):
        self.__bluetooth = bluetooth
        self.__body_stats_df['time'] = timedelta(0)
        self.lock = threading.Lock()
        self.__bluetooth.register_patient_status_observers(self.send_patient_status)
        pass

    def set_body_stats_df(self, new_df):
        self.lock.acquire()
        try:
            self.__body_stats_df = new_df
        finally:
            self.lock.release()

    def get_body(self):
        return self.__body

    def get_body_stats_df(self):
        return self.__body_stats_df

    def get_body_stats_df_json(self):
        temp = self.__body_stats_df.to_json()
        return temp

    def get_patient_info_json(self):
        temp = json.dumps(self.__body)
        return temp

    def get_patient_history(self):
        return self.__patient_history

    def get_patient_history_json(self):
        temp = json.dumps(self.__patient_history)
        return temp

    def set_patient_history_json(self, new_patient_history):
        temp = json.loads(new_patient_history)
        self.__patient_history = temp
        return

    def send_patient_status(self):
        data = self.get_patient_info_json()
        self.__bluetooth.enqueue_bluetooth_data(data, config_bluetooth['PATIENT_STATUS_HEADER'])
        return
