import ast
import pandas as pd
import numpy as np
import scipy.sparse as sparse


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


def load_sensor_dataframe(file):
    try:
        df = pd.read_csv(file, index_col=0)
        df1 = df["readings"]
        data = extract_sensor_dataframe(df["readings"])
        # temp = np.asarray(data, dtype=np.float64)
        # df["reading"] = data
        # df1 = df["reading"]
        # np.reshape(temp, (64, 27))
        # arr = sparse.coo_matrix(temp, shape=(64, 27))
        # df1 = df["readings"]
        # df2 = df1.apply(lambda r: tuple(r), axis=1).apply(np.array)
        # df["readings"] = df1.apply(lambda r: tuple(r), axis=1).apply(np.array)

        # for index, row in df.iterrows():
        #     temp = pd.DataFrame(row).T
        #     data = extract_sensor_dataframe(temp)
        #     df.at[index, "data"] = data.astype(float)

        return df
    except FileNotFoundError as e:
        print("Invalid File: {}".format(e))
    else:
        return None
