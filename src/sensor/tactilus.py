import json
import random
import time
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from threading import Thread
from datetime import datetime, timedelta
from sseclient import SSEClient
import os
from os.path import isfile, join, realpath, dirname
import configparser
import requests

dir_path = dirname(realpath(__file__))
file = join(dir_path, '../configuration/config.ini')
config = configparser.ConfigParser()
config.read(file)
config_bed = config['BED']


# This class will be used when we have access to the api to get sensor data
def save_sensor_data(df: pd.DataFrame):  # should I leave it all this way or try and add some stuff to configuration?
    directory = os.getcwd()
    temp = "{}/sensor_data".format(directory)
    files = os.listdir(r"{}/src/data".format(directory))
    index1 = files[(len(files) - 1)][21:]
    index = int(files[(len(files) - 1)][21:][:len(index1) - 4])
    df.to_csv("{}/test_files/sensor_data_dataframe{}.csv".format(temp, index + 1))


def save_data_to_db(data):
    url = "https://test.api.jacksonmed.org/sensor-data"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, data=json.dumps(data), headers=headers)


def create_data_to_be_inserted(path, file_name, is_patient_present):
    date_time = datetime.now()
    temp_data = json.load(open(path + "/" + file_name))
    temp_data["frequency"] = 3600
    data = {
        "date": str(date_time.date()),
        "hour": str(date_time.hour),
        "min": str(date_time.minute),
        "sec": str(date_time.second),
        "data": json.dumps(temp_data),
        "patient_present": is_patient_present
    }
    return data


def insert_data(compiled_data_path, is_patient):
    files = [f for f in os.listdir(compiled_data_path) if
             os.path.isfile(os.path.join(compiled_data_path, f))]
    for file_name in files:
        data = create_data_to_be_inserted(compiled_data_path, file_name, is_patient)
        save_data_to_db(data)
        os.remove(compiled_data_path + "/" + file_name)


def bool_based_on_probability(probability=0.5):
    return random.random() < probability


def is_patient_present(data):
    temp = sum(x > 12 for x in data)
    if temp > 10:
        return True
    else:
        return False


def remove_files_from_directory(path):
    files = [f for f in os.listdir(path) if
             os.path.isfile(os.path.join(path, f))]
    for file_name in files:
        os.remove(path + "/" + file_name)


class PressureSensor(Thread):
    dt_string = "%d-%m-%Y_%H:%M:%S"

    def __init__(self, file_count):
        if os.uname()[2][:3] == 'arm':
            self.isRaspberryPi = True
        else:
            self.isRaspberryPi = True
        self.file_count = file_count
        Thread.__init__(self, target=self.run())

    def run(self):
        if self.isRaspberryPi:
            self.start_sse_client()
        else:
            self.start_dummy_sse_client()

    def start_sse_client(self):
        is_patient_previous = False
        directory = os.getcwd()
        raw_data_path = directory + "/data/cole"
        compiled_data_path = directory + "/data/compiled_data"

        remove_files_from_directory(raw_data_path)
        remove_files_from_directory(compiled_data_path)
        if self.isRaspberryPi:
            url = config_bed['URL']
            sse = SSEClient(url)
            for response in sse:
                df = pd.read_json(response.data)
                # save_sensor_data(df)
                if "readings" in df.columns:
                    print("data received")
                    self.save_sensor_data_json(df, raw_data_path)

                    # is_patient_current = is_patient_present(df["readings"][0])
                    #
                    # if not is_patient_current and is_patient_previous:
                    #     print("Patient has exited the bed time: ", datetime.now())
                    #     self.convert_data_single_json(raw_data_path, compiled_data_path)
                    #     insert_data(compiled_data_path, is_patient_current)
                    # elif is_patient_current and not is_patient_previous:
                    #     print("Patient has entered the bed time: ", datetime.now())
                    #     self.convert_data_single_json(raw_data_path, compiled_data_path)
                    #     insert_data(compiled_data_path, is_patient_current)
                    # elif is_patient_current and is_patient_previous and bool_based_on_probability(0.01):
                    #     print("Random Patient In Bed Data Sending to Db time: ", datetime.now())
                    #     self.convert_data_single_json(raw_data_path, compiled_data_path)
                    #     insert_data(compiled_data_path, is_patient_current)
                    #
                    # is_patient_previous = is_patient_current

    def start_dummy_sse_client(self):
        directory = os.getcwd()
        path = "{}/../tests/test_files/sensor_data".format(directory)
        num_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
        raw_data_path = directory + "/data/raw_data"
        compiled_data_path = directory + "/data/compiled_data"

        remove_files_from_directory(raw_data_path)
        remove_files_from_directory(compiled_data_path)

        while True:
            random_number = random.randint(0, num_files)
            file_name = path + "/sensor_data_dataframe{}.csv".format(random_number)
            df = pd.read_csv(file_name)
            self.save_sensor_data_json(df, raw_data_path)
            self.convert_data_single_json(raw_data_path, compiled_data_path)

            files = [f for f in os.listdir(compiled_data_path) if os.path.isfile(os.path.join(compiled_data_path, f))]
            for file_name in files:
                data = create_data_to_be_inserted(compiled_data_path, file_name, bool_based_on_probability(0.1))
                save_data_to_db(data)
                os.remove(compiled_data_path + "/" + file_name)
            time.sleep(1)

    def save_sensor_data_json(self, df: pd.DataFrame,
                              path):  # should I leave it all this way or try and add some stuff to configuration?
        now = datetime.utcnow().isoformat(sep=' ', timespec='milliseconds')
        # dt_string = now.strftime(self.dt_string)

        file_name = "{}/{}_sensor_data.json".format(path, now)
        df.to_json(file_name)
        # self.validate_data_directory(path)

    def validate_data_directory(self, path):
        num_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

        while num_files > self.file_count:
            num_files = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
            file_to_delete = self.get_oldest_file(path)
            os.remove(file_to_delete)

    def get_oldest_file(self, path):
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        oldest_file = ""

        for file_name in files:
            old_date = self.get_date_from_file(oldest_file)
            date = self.get_date_from_file(file_name)
            if old_date is None or date < old_date:
                oldest_file = file_name
        return path + "/" + oldest_file

    def get_date_from_file(self, file_name):
        if file_name == "":
            return None
        date_string = file_name[0:19]
        return datetime.strptime(date_string, self.dt_string)

    def convert_data_single_json(self, raw_data_path, compiled_data_path):
        now = datetime.now()
        dt_string = now.strftime(self.dt_string)
        file_name = dt_string + "_" + str(self.file_count) + "_compiled_data.json"

        save_path = compiled_data_path + "/" + file_name
        files = [f for f in os.listdir(raw_data_path) if os.path.isfile(os.path.join(raw_data_path, f))]
        df = pd.DataFrame()
        index = 0
        for file_name in files:
            sensor_data = pd.read_json(raw_data_path + "/" + file_name)["readings"].values
            temp_df = pd.DataFrame({'index': index, 'data': sensor_data})
            df = df.append(temp_df)
            index = index + 1
        df = df.set_index('index')
        df.to_json(save_path)
