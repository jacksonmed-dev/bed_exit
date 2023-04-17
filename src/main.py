# import threading
#
# from src.sensor.tactilus import PressureSensor
#
# if __name__ == "__main__":
#     thread = PressureSensor(file_count=60)
#     thread.start()
import json

from sseclient import SSEClient
import threading


def start_api_sse_client():
    url = "http://10.0.0.1/api/sse"
    sse = SSEClient(url)
    for response in sse:
        data = response.data.strip()
        if data:
            json_data = json.loads(data)
            if 'id' in json_data:
                id = json_data['id']
                print("ID:", id)
            else:
                print("No ID in response.")


def start_api_monitor_sse_client():
    url = "http://10.0.0.1/api/monitor/sse"
    sse = SSEClient(url)
    for response in sse:
        if response.event == 'body':
            data = response.data.strip()
            present_field = json.loads(data)['present']
            print(present_field)



if __name__ == '__main__':
    thread = threading.Thread(target=start_api_monitor_sse_client)
    thread.start()
    print("API SSE Client started on a separate thread.")
