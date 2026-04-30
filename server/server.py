import socket
import threading

HOST = "0.0.0.0" # AWS üzerinde tüm arayüzleri dinlemek için doğru seçim
PORT = 6060

class BattleShipServer:
    def __init__(self):
        self.clients = []
        self.player_data = {} # Oyuncu tahtalarını ve durumlarını tutar
        self.turn = 0 # Sıra Player 0'da başlar
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        player_index = -1
        with self.lock:
            player_index = len(self.clients)
            self.clients.append(conn)
        
        print(f"Oyuncu {player_index} bağlandı: {addr}")
        conn.send(f"PLAYER:{player_index}".encode())

        while True:
            try:
                data = conn.recv(4096).decode()
                if not data:
                    break
                
                print(f"Oyuncu {player_index} mesajı: {data}")
                self.process_command(player_index, data)
                
            except Exception as e:
                print(f"Hata: {e}")
                break

        print(f"Bağlantı kesildi: {player_index} ({addr})")
        with self.lock:
            if conn in self.clients:
                self.clients.remove(conn)
        conn.close()

    def process_command(self, p_idx, data):
        """Oyun mantığını burada yönetiyoruz[cite: 1, 2]"""
        if data.startswith("READY:"):
            # Oyuncudan gelen gemi dizilimini kaydet
            self.player_data[p_idx] = data.split(":")[1]
            print(f"Oyuncu {p_idx} hazır.")
            # İki oyuncu da hazırsa oyunu başlat
            if len(self.player_data) == 2:
                self.broadcast("START:0") # Sıranın Player 0'da olduğunu bildir

        elif data.startswith("ATTACK:"):
            # Sıra kontrolü
            if p_idx == self.turn:
                # Gelen saldırıyı diğer oyuncuya ilet
                target_idx = 1 if p_idx == 0 else 0
                self.clients[target_idx].send(data.encode())
                # Sırayı değiştir
                self.turn = target_idx
                self.broadcast(f"TURN:{self.turn}")

        elif data.startswith("RESULT:"):
            # Vuruş sonucunu (HIT/MISS) diğerine ilet
            target_idx = 1 if p_idx == 0 else 0
            self.clients[target_idx].send(data.encode())

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                pass

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(2)
        print(f"Amiral Battı Sunucusu {PORT} portunda çalışıyor...")

        while True:
            conn, addr = server.accept()
            if len(self.clients) < 2:
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
            else:
                conn.send("ERROR:Sunucu dolu".encode())
                conn.close()

if __name__ == "__main__":
    server = BattleShipServer()
    server.start()