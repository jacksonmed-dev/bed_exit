import ast
from unittest import TestCase
import pandas as pd
from bed.sensor.util.sensor_data_utils import extract_sensor_dataframe, load_sensor_dataframe
from pandas._testing import assert_frame_equal


class Test(TestCase):
    def test_extract_sensor_dataframe(self):
        # First test: Data correct format
        test_file = "../test_files/temp/data.csv"
        df = pd.read_csv(test_file, index_col=0)

        data = df["data"].iloc[0]
        if type(data) == str:
            data = ast.literal_eval(data)
        df_correct = pd.DataFrame(data)

        test_df = extract_sensor_dataframe(df)

        assert_frame_equal(df_correct, test_df)

        # Second Test: Incorrect data format that is commonly used throughout the program
        test_file = "../test_files/temp/incorrect_data_format.csv"
        df = pd.read_csv(test_file, index_col=0)
        self.assertEqual(None, extract_sensor_dataframe(df))

    def test_load_sensor_dataframe(self):
        # First Test is a dataframe with one entry
        test_file_correct = "../test_files/temp/data.csv"
        correct_df = pd.read_csv(test_file_correct, index_col=0)
        data = extract_sensor_dataframe(correct_df)
        correct_df.at[correct_df.index.values[0], "data"] = data.astype(float)

        test_df = load_sensor_dataframe(test_file_correct)
        assert_frame_equal(correct_df, test_df)
        test_df.to_csv("test_files/incorrect_data_format.csv")

        # Second test is a df with bad file path
        test_file_incorrect = "test_files/wrong_file.csv"
        temp = load_sensor_dataframe(test_file_incorrect)
        self.assertEqual(None, temp)

        # Third test is a dataframe with multiple entries
        test_file_multiple = "../test_files/temp/data_multiple_entries.csv"
        correct_df = pd.read_csv(test_file_multiple, index_col=0)
        for index, row in correct_df.iterrows():
            temp = pd.DataFrame(row).T
            data = extract_sensor_dataframe(temp)
            correct_df.at[index, "data"] = data.astype(float)

        test_df = load_sensor_dataframe(test_file_multiple)

        assert_frame_equal(correct_df, test_df)
