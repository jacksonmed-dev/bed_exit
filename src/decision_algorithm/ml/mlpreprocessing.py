import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from os.path import isfile, join, realpath, dirname

dir_path = dirname(realpath(__file__))
all_files = glob.glob(dir_path + "/data/features*.csv")
df = pd.concat(map(pd.read_csv, all_files), ignore_index=True)
df.to_csv('data/finaldata.csv',index_label=False)