import unittest
from pandas._testing import assert_frame_equal

import pandas as pd

import os
import sys

import configparser
dir_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(dir_path, '../../src/configuration/config_for_tests.ini')
config = configparser.ConfigParser()
config.read(file)

full_path = os.path.join(dir_path, config['PATHS']['ML'])
sys.path.append(os.path.abspath(full_path))

import feature_extraction_preprocessing as fep


class TestFeatureExtractionPreprocessing(unittest.TestCase):
    def setUp(self):
        self.patient_history_feature_df1 = pd.DataFrame([[36, 0, 1, 19, 2, 0, 1, 0, 0, 1, 0, 5, 101.2, 1, 1, 0, 125, 77, 0]], index=['data'],
                              columns=['age', 'age_cat', 'sex', 'BMI', 'BMI_cat', 'ulcer_head',
                                       'ulcer_arm', 'ulcer_shoulder', 'ulcer_buttocks',
                                       'ulcer_leg', 'ulcer_heel',
                                       'ICU_stay', 'temp',
                                       'fever', 'diabetes_typeI', 'diabetes_typeII',
                                       'sys_pressure',
                                       'dia_pressure',
                                       'blood_pressure_cat'])

        self.combined_df1= pd.DataFrame([[36, 0, 1, 19, 2, 0, 1, 0, 0, 1, 0, 5, 101.2, 1, 1, 0, 125, 77, 0,2,2,2,2,2,2,12,"high"]], index=['data'],
                              columns=['age', 'age_cat', 'sex', 'BMI', 'BMI_cat', 'ulcer_head',
                                       'ulcer_arm', 'ulcer_shoulder', 'ulcer_buttocks',
                                       'ulcer_leg', 'ulcer_heel',
                                       'ICU_stay', 'temp',
                                       'fever', 'diabetes_typeI', 'diabetes_typeII',
                                       'sys_pressure',
                                       'dia_pressure',
                                       'blood_pressure_cat', 'activity', 'friction', 'mobility', 'moisture',
                                       'nutrition', 'sensory', 'Braden', 'risk'])
        pass

    def tearDown(self):
        pass

    def test_patient_history_feature_extraction_df(self):
        assert_frame_equal(fep.patient_history_feature_extraction_df(), self.patient_history_feature_df1)

    def test_combine_features_df(self):
        assert_frame_equal(fep.combine_features_df(), self.combined_df1)

if __name__ == '__main__':
    unittest.main()
