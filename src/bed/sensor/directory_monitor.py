import sys
import threading

import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from bed.bed import Bed
from bed.sensor.util.sensor_data_utils import extract_sensor_dataframe
from massage.massage import Massage
from body.body import Patient
import os


# Check to make sure the file is not empty!!!
class OnMyWatch(threading.Thread):
    # Set the directory on watch
    __observer = Observer()

    def __init__(self, path, bed: Bed):
        self.__watch_directory = path
        self.__bed = bed
        self.__event_handler = Handler(self.__bed, path)

    def run(self):
        print("Directory Monitor Started")
        self.__observer.schedule(self.__event_handler, self.__watch_directory, recursive=True)
        self.__observer.start()
        # self.__observer.join()

    def stop(self):
        self.__observer.stop()

    def get_observer(self):
        return self.__observer

    def get_watch_directory(self):
        return self.__watch_directory

    def set_watch_directory(self, path):
        self.__watch_directory = path


class Handler(FileSystemEventHandler):
    def __init__(self, bed: Bed, path):
        self.__bed = bed
        self.__file = path + "/data.csv"
        # Fix the file path!!!! Should I put permanent file path into configuration?

    def on_modified(self, event):
        df = pd.read_csv(self.__file, index_col=0)
        data = extract_sensor_dataframe(df)

        df.at[df.index.values[0], "data"] = data.astype(float)
        sensor = self.__bed.get_pressure_sensor()
        sensor.append_sensor_data(df)
        sensor.set_current_frame(df)
        self.__bed.analyze_sensor_data()
        self.__bed.print_stats()
        # print("Directory Modified - %s" % event.src_path)

