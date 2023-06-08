import bluetooth


class BluetoothService:
    def __init__(self):
        self.server_socket = None
        self.client_socket = None

    def start_service(self):
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_socket.bind(("", bluetooth.PORT_ANY))
        self.server_socket.listen(1)
        port = self.server_socket.getsockname()[1]
        print("Service started. Listening on port", port)

        self.client_socket, client_address = self.server_socket.accept()
        print("Accepted connection from", client_address)

    def stop_service(self):
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        print("Service stopped")

    def receive_data(self):
        data = self.client_socket.recv(1024)
        print("Received:", data.decode())