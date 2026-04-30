import socket

class Network:
    def __init__(self, ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, int(port)))

    def send(self, data):
        try:
            self.client.send(str(data).encode())
            # return self.client.recv(1024).decode()#
        except Exception as e:
           print(f"Bağlantı hatası:{e}")