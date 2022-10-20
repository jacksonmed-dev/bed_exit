import unittest
import os
from os.path import isfile, join


class MyTestCase(unittest.TestCase):
    def test_something(self):

        dir_path = os.path.dirname(os.path.realpath(__file__))
        full_path = os.path.join(dir_path, "Insert Relative Path Here")
        onlyfiles = [f for f in os.listdir(full_path) if isfile(join(full_path, f))]
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
