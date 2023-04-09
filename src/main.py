import threading

from src.sensor.tactilus import PressureSensor

if __name__ == "__main__":
    thread = PressureSensor(file_count=60)
    thread.start()
