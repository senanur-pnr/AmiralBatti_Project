import socket

class Network:
    def __init__(self, ip, port=6060):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ip
        self.port = port
        self.addr = (self.server, self.port)
        self.id = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Sunucudan gelen ilk mesajı (ID) al
            return self.client.recv(2048).decode()
        except Exception as e:
            print(f"Baglanti hatasi: {e}")
            return None

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(f"Gonderim hatasi: {e}")
            return None