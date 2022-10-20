import threading


if __name__ == "__main__":
    threading.Thread(target=bed.get_pressure_sensor().start_sse_client).start()
