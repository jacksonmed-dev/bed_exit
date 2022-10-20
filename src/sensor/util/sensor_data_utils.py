import ast
import pandas as pd


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
        return df
    except FileNotFoundError as e:
        print("Invalid File: {}".format(e))
    else:
        return None
