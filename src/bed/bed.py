import json

import pandas as pd
from bed.sensor.tactilus import PressureSensor
from body.body import Patient
from bed.sensor.util.sensor_data_utils import extract_sensor_dataframe
from datetime import timedelta
import numpy as np
from massage.massage import Massage
from configuration import config, is_raspberry_pi

config_blue = config['BLUETOOTHCONNECTION']

if is_raspberry_pi:
    from bed.sensor.gpio import Gpio
    from bluetoothconnection.bluetooth_connection import Bluetooth
else:
    from bed.sensor.dummy_gpio import Gpio
    from bluetoothconnection.bluetooth_connection_dummy import Bluetooth


# A bed contains the following:
#   Patient
#   Sensor
#   Relays to control the valves
#   Massage Functionality
class Bed:
    # Same value for inflatable_regions and relay count. There may be a situation where there are more relays than
    # inflatable regions. For now, the variable serves no purpose
    __inflatable_regions = 8
    __relay_count = 8
    __bed_gpio = Gpio(inflatable_regions=__inflatable_regions)
    __pressure_sensor = PressureSensor(__inflatable_regions)
    __bed_stats_automatic = False
    # __body_stats_df = pd.DataFrame(0, index=['head', 'shoulders', 'back', 'butt', 'calves', 'feet'],
    #                                columns=['time', 'max_pressure'])

    __massage = Massage(__bed_gpio)

    def __init__(self, patient: Patient, bluetooth: Bluetooth):
        self.__patient = patient
        self.__bluetooth = bluetooth
        self.__pressure_sensor.register_callback(self.analyze_sensor_data)
        self.__bluetooth.register_bed_massage_callback(self.massage)
        self.__bed_gpio.register_observer(self.send_bed_status_bluetooth)
        return

    def extract_sensor_dataframe(df):
        data = df.iloc[0]
        try:
            if type(data) == str:
                data = ast.literal_eval(data)
            # df = pd.DataFrame(data)
            return data
        except Exception as e:
            print(e)
        else:
            return None

    # Main algorithm to make decision. Only looks at time spent under "high pressure"
    def analyze_sensor_data(self):
        #### Work on this ###
        ### function should generate a dataframe with pressure regions ###
        body_stats_df = self.__patient.get_body_stats_df()
        time_diff = self.__pressure_sensor.get_time()
        temp = self.__pressure_sensor.get_current_frame()
        if temp.empty:
            return
        # data = extract_sensor_dataframe(df["readings"])
        # test = self.__pressure_sensor.get_current_frame()['readings']
        data = np.asarray(extract_sensor_dataframe(self.__pressure_sensor.get_current_frame()['readings']),
                          dtype=np.float64).reshape(64, 27)
        # temp = np.asarray(data, dtype=np.float64).reshape(64,27)
        # temp = np.asarray(test, dtype=np.float64)
        sensor_data = pd.DataFrame(data)

        sensor_composition = self.__pressure_sensor.get_sensor_body_composition()

        # Identify regions of the body that are in a high pressure state
        for body_part, value in sensor_composition.items():
            data = sensor_data.loc[value]
            max_value = data.max().max()
            body_stats_df.at[body_part, 'max_pressure'] = max_value

            if max_value > self.__pressure_sensor.get_sensor_threshold():
                current_time = body_stats_df.at[body_part, 'time']
                new_time = current_time + time_diff
                body_stats_df.at[body_part, 'time'] = new_time
            else:
                body_stats_df.at[body_part, 'time'] = timedelta(0)

        # Update the patient body stats dataframe
        self.__patient.set_body_stats_df(body_stats_df)

        # Demo method!!
        for body_part, value in sensor_composition.items():
            pressure = body_stats_df.at[body_part, 'max_pressure']
            if pressure > self.__pressure_sensor.get_sensor_threshold():
                self.calculate_deflatable_regions(body_part)
            else:
                self.calculate_inflatable_regions(body_part)

        self.__bed_gpio.change_relay_state()
        return

    # Should be pre computed. Change this!!! Save in dictionary. Should only called if the body region state needs to
    # change
    def calculate_deflatable_regions(self, body_part):
        sensor_region_body = self.__pressure_sensor.get_sensor_body_composition()[body_part]
        sensor_data_df = \
            pd.DataFrame(np.array(self.__pressure_sensor.get_current_frame()['readings'][0]).reshape(64, 27)).loc[
                sensor_region_body]

        sensor_data_row_max = sensor_data_df.max(axis=1)
        sensor_data_row_max_indices = sensor_data_row_max.index.tolist()

        sensor_threshold = self.__pressure_sensor.get_sensor_threshold()
        for index, array in enumerate(self.__pressure_sensor.get_sensor_inflatable_composition()):
            if any(x in sensor_data_row_max for x in array):
                # temp2 = [x for x in sensor_data_max_index if x in array]
                max_sensor_value = sensor_data_row_max[[x in array for x in sensor_data_row_max_indices]].max()
                if max_sensor_value > sensor_threshold:
                    self.__bed_gpio.set_relay(pin=index, state=0)
        return

    def calculate_inflatable_regions(self, body_part):
        sensor_region_body = self.__pressure_sensor.get_sensor_body_composition()[body_part]
        sensor_data_df = \
            pd.DataFrame(np.array(self.__pressure_sensor.get_current_frame()['readings'][0]).reshape(64, 27)).loc[
                sensor_region_body]

        sensor_data_row_max = sensor_data_df.max(axis=1)

        for index, array in enumerate(self.__pressure_sensor.get_sensor_inflatable_composition()):
            if any(x in sensor_data_row_max for x in array):
                self.__bed_gpio.set_relay(pin=index, state=1)
        return

    def send_bed_status_bluetooth(self):
        data = str(self.generate_bed_status_json())
        self.__bluetooth.enqueue_bluetooth_data(data, header_string=config_blue['BED_STATUS_RESPONSE'])

    def send_bed_status_automatic_bluetooth(self):
        if self.__bed_stats_automatic:
            data = str(self.generate_bed_status_json())
            self.__bluetooth.enqueue_bluetooth_data(data, header_string=config_blue['BED_STATUS_RESPONSE'])

    def print_stats(self):
        print("Directory Modified")
        print("Body Stats:\n{}\n".format(self.__patient.get_body_stats_df()))
        print("Relays:\t{}\n\n".format(self.__bed_gpio.get_gpio_pins()))

    # Getters/Setters

    def get_massage(self):
        return self.__massage

    def get_pressure_sensor(self):
        return self.__pressure_sensor

    def get_relay_count(self):
        return self.__relay_count

    def get_patient(self):
        return self.__patient

    def get_inflatable_regions(self):
        return self.__inflatable_regions

    def get_gpio(self):
        return self.__bed_gpio

    def set_pressure_sensor(self, pressure_sensor: PressureSensor):
        self.__pressure_sensor = pressure_sensor

    def set_relay_count(self, relay_count):
        self.__relay_count = relay_count

    def set_patient(self, patient: Patient):
        self.__patient = patient

    def set_inflatable_regions(self, count):
        self.__inflatable_regions = count

    def set_new_massage(self):
        self.__massage = Massage(gpio=self.__bed_gpio)

    def get_bluetooth(self):
        return self.__bluetooth

    def set_bed_stats_automatic(self):
        if self.__bed_stats_automatic:
            self.__bed_stats_automatic = False
        else:
            self.__bed_stats_automatic = True
        print("Bed Stats Automatic: {}".format(self.__bed_stats_automatic))

    def generate_bed_status_json(self):
        gpio = self.__bed_gpio.get_gpio_pins()
        json_final = json.dumps({
            "gpio_pins": [value for key, value in gpio.items()],
        })
        return json_final

    def massage(self, state):
        if state == 0:
            self.stop_massage()
        if state == 1:
            self.set_new_massage()
            self.__massage.set_massage_status(True)
            self.__massage.start()

    def stop_massage(self):
        self.__massage.set_massage_status(False)
