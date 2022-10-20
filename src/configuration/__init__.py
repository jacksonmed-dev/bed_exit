import configparser
import os
from os.path import join

dir_path = os.getcwd()
file = join(dir_path, 'configuration/config.ini')
config = configparser.ConfigParser()
config.read(file)

file2 = join(dir_path, "configuration/config_for_tests.ini")
test_config = configparser.ConfigParser()
test_config.read(file2)

is_raspberry_pi = False

if os.uname()[4][:3] == 'arm' and "Linux" in os.uname().nodename:
    is_raspberry_pi = True

