import socket

class Network:
    def __init__(self, server_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip # LoginWindow'dan gelen IP
        self.port = 5555
        self.addr = (self.server, self.port)
        self.player_id = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            # Bağlantı başarılıysa sunucu oyuncu numarasını (0 veya 1) gönderir
            return self.client.recv(2048).decode()
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return None

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(e)
            return None