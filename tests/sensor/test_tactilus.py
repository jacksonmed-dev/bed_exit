from unittest import TestCase
from bed.bed import Bed
from body.body import Patient
from bed.sensor.util.sensor_data_utils import load_sensor_dataframe
from pandas._testing import assert_frame_equal
from bluetoothconnection.bluetooth_connection_dummy import Bluetooth as Bluetooth
from datetime import timedelta
import pandas as pd
import os


class TestPressureSensor(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_file = "../test_files/sensor_data/sensor_data_dataframe8.csv"
        bluetooth = Bluetooth()
        cls.bed = Bed(patient=Patient(bluetooth=bluetooth), bluetooth=bluetooth)
        data_df = load_sensor_dataframe(cls.test_file)
        cls.sensor = cls.bed.get_pressure_sensor()
        cls.sensor.append_sensor_data(data_df)
        cls.sensor.set_current_frame(data_df)

    def test_append_sensor_data(self):
        current_frame_df = self.bed.get_pressure_sensor().get_current_frame()
        sensor_data_df = self.bed.get_pressure_sensor().get_sensor_data()
        self.bed.get_pressure_sensor().append_sensor_data(current_frame_df)

        correct_df = sensor_data_df.append(current_frame_df)

        assert_frame_equal(correct_df, self.bed.get_pressure_sensor().get_sensor_data())

    def test_get_time(self):
        # Test 1: Correct format. Time delta should be one day
        file = "../test_files/temp/data_multiple_entries.csv"
        bed = Bed(patient=Patient())
        data_df = load_sensor_dataframe(file)
        sensor = bed.get_pressure_sensor()
        sensor.set_sensor_data(data_df)
        time_diff = sensor.get_time()

        self.assertEqual(timedelta(days=1), time_diff)

        # Second test: data_df contains one entry. if len(data) <= 1
        file = "../test_files/temp/data.csv"
        data_df = load_sensor_dataframe(file)
        sensor.set_sensor_data(data_df)
        time_diff = sensor.get_time()

        self.assertEqual(timedelta(0), time_diff)

        # Third Test: Sensor data is type None.
        sensor.set_sensor_data(None)
        time_diff = sensor.get_time()
        self.assertEqual(None, time_diff), "time difference type should be None, recieved {}".format(type(time_diff))

        # Fourth test: Date in in the wrong format
        file = "../test_files/temp/incorrect_date_format.csv"
        data_df = load_sensor_dataframe(file)
        sensor.set_sensor_data(data_df)
        time_diff = sensor.get_time()

        self.assertEqual(None, time_diff), "time difference type should be None, recieved {}".format(type(time_diff))

    def test_sensor_sse(self):
        self.sensor.start_sse_client()

    def test_save_sensor_data(self):
        df = pd.DataFrame()
        self.sensor.save_sensor_data(df)

