import unittest
from pandas._testing import assert_frame_equal

import pandas as pd
import os
import sys

import configparser
dir_path = os.path.dirname(os.path.realpath(__file__))
file = os.path.join(dir_path, '../../src/configuration/config.ini')
config = configparser.ConfigParser()
config.read(file)

print(config.sections())

full_path = os.path.join(dir_path, config['PATHS']['ML'])
sys.path.append(os.path.abspath(full_path))

from pprint import pprint
pprint(sys.path)

from braden_score import BradenScore


class TestBradenScore(unittest.TestCase):

    def setUp(self):
        self.scores1 = pd.DataFrame([2, 2, 2, 2, 2, 2],
                                    index=['activity', 'friction', 'mobility', 'moisture', 'nutrition', 'sensory'],
                                    columns=['score'])
        self.bradenScore1 = 12
        self.risk1 = "high"
        self.new_input1 = pd.DataFrame([4, 4, 2, 4, 4, 4],
                                       index=['activity', 'friction', 'mobility', 'moisture', 'nutrition', 'sensory'],
                                       columns=['score']).to_json()
        self.braden_df1 = pd.DataFrame([[2, 2, 2, 2, 2, 2, 12, "high"]],
                                       index=['score'],
                                       columns=['activity', 'friction', 'mobility', 'moisture', 'nutrition', 'sensory',
                                                'Braden',
                                                'risk'])
        self.braden_df2 = pd.DataFrame([[4, 4, 2, 4, 4, 4, 22, "mild"]],
                                       index=['score'],
                                       columns=['activity', 'friction', 'mobility', 'moisture', 'nutrition', 'sensory',
                                                'Braden',
                                                'risk'])
        pass

    def tearDown(self):
        pass

    def test_get_scores(self):
        assert_frame_equal(BradenScore().get_scores(), self.scores1)

    def test_get_braden_score(self):
        self.assertEqual(BradenScore().get_braden_score(), self.bradenScore1)

    def test_get_risk(self):
        self.assertEqual(BradenScore().get_risk(), self.risk1)

    def test_get_braden_df(self):
        assert_frame_equal(BradenScore().get_braden_df(), self.braden_df1)

    def test_set_scores_recalculate(self):
        assert_frame_equal(BradenScore(self.new_input1).get_braden_df(), self.braden_df2)


if __name__ == '__main__':
    unittest.main()
