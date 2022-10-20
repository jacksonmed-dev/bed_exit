from unittest import TestCase
from bed.bed import Bed
from bed.sensor.util.sensor_data_utils import load_sensor_dataframe
from body.body import Patient
import os
from bluetoothconnection.bluetooth_connection_dummy import Bluetooth as Bluetooth

# if os.uname()[4][:3] == 'arm':
#     path = "/home/pi/Desktop/sensor_data"
#     from bluetoothconnection.bluetooth_connection import Bluetooth as Bluetooth
#
# else:
#     path = "/home/cjstanfi/Desktop/sensor_data"
#     from bluetoothconnection.bluetooth_connection_dummy import Bluetooth as Bluetooth

class TestBed(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.test_file = "../test_files/sensor_data/sensor_data_dataframe8.csv"
        bluetooth = Bluetooth()
        cls.bed = Bed(patient=Patient(bluetooth=bluetooth), bluetooth=bluetooth)
        data_df = load_sensor_dataframe(cls.test_file)
        sensor = cls.bed.get_pressure_sensor()
        sensor.append_sensor_data(data_df)
        sensor.set_current_frame(data_df)
        # cls.bed.analyze_sensor_data()


    def test_analyze_sensor_data(self):
        self.bed.analyze_sensor_data()
        self.fail()

    def test_calculate_deflatable_regions(self):
        self.fail()

    def test_calculate_inflatable_regions(self):
        self.fail()

    def test_print_stats(self):
        self.fail()

    def test_generate_bed_status_json(self):
        bed = self.bed
        bed.generate_bed_status_json()
        return

    def test_bed_status_callback(self):
        self.bed.get_bluetooth().register_bed_status_callback(self.bed.send_bed_status_bluetooth)
        data = b'#'
        self.bed.get_bluetooth().receive_data(data)
        self.bed.send_bed_status_bluetooth()

