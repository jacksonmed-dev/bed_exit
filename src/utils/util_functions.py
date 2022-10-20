import ast
import pathlib
from datetime import datetime
import numpy as np
from matplotlib import pyplot as plt
from configuration import config

config_paths = config['PATHS']


def save_df(self, i, df):
    current_path = str(pathlib.Path(__file__).parent.resolve())
    print(current_path)
    path = config_paths['DATA']
    filename = "data" + str(i) + ".csv"
    df.to_csv(current_path + path + filename)


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


# Write Unit Test for this
def convert_sensor_data_to_png(df):
    file_name = "sensor_data_image_{}.png".format(datetime.now().strftime("%m/%d/%Y, %H: %M:%S"))
    data = np.asarray(extract_sensor_dataframe(df['readings']), dtype=np.float64).reshape(64, 27)
    plt.axis('scaled')
    plt.pcolormesh(data, cmap='hot')
    plt.axis('off')
    plt.savefig("./test_files/test_image/" + file_name)
    print("Generated image: {}".format(file_name))
