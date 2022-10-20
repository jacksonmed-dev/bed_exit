import unittest
import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(dir_path, "../../src/decision_algorithm/ml/"))
import model
import preprocessing
from zipfile import ZipFile

MODEL_DIR = os.path.join(dir_path, "../src/decision_algorithm/ml/training/model_file")
with ZipFile(MODEL_DIR + '/mask_rcnn_body parts_0050.zip', 'r') as zipObj:
   zipObj.extractall(MODEL_DIR)
MODEL_DIR = os.path.join(dir_path, "../src/decision_algorithm/ml/training/model_file/mask_rcnn_body parts_0050.h5")
TEST_DIR = os.path.join(dir_path, "../test_files/sensor_data/sensor_data_dataframe237.csv")
IMAGE_DIR = os.path.join(dir_path, "../../src/decision_algorithm/ml/test_img/237.png")# change your file path here
sys.path.append("../../src/decision_algorithm/ml")
class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(preprocessing.convert_to_image(TEST_DIR), True)  # add assertion here
        a = {"head": [[[10, 51], [10, 56], [15, 51], [15, 56]]]}
        #print(a.items())
        #print(model.Model().load_model(IMAGE_DIR,MODEL_DIR).items())

        self.assertEqual(model.Model().load_model(IMAGE_DIR,MODEL_DIR), {'head': [[[10, 51], [10, 56], [15, 51], [15, 56]]], 'shoulder': [], 'buttocks': [], 'leg': [[[42, 42], [42, 49], [55, 42], [55, 49]], [[42, 53], [42, 59], [54, 53], [54, 59]]], 'arm': [[[8, 61], [8, 65], [14, 61], [14, 65]], [[9, 38], [9, 42], [13, 38], [13, 42]]], 'heel': []})  # add assertion here
        self.assertLessEqual(a.items(), model.Model().load_model(IMAGE_DIR,MODEL_DIR).items())
if __name__ == '__main__':
    unittest.main()
    #model.load_model()
