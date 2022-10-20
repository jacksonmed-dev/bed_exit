import os
import threading
from bed.bed import Bed
from body.body import Patient
from server.flask_server import create_server
from configuration import is_raspberry_pi

if is_raspberry_pi:
    from bluetoothconnection.bluetooth_connection import Bluetooth as Bluetooth
else:
    from bluetoothconnection.bluetooth_connection_dummy import Bluetooth as Bluetooth

if __name__ == "__main__":

    bluetooth = Bluetooth()
    p = Patient(bluetooth=bluetooth)
    bed = Bed(patient=p, bluetooth=bluetooth)
    app = create_server(bed=bed, bluetooth=bluetooth)

    threading.Thread(target=bed.get_pressure_sensor().start_sse_client).start()
