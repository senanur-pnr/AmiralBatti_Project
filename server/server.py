import socket
import threading

HOST = "0.0.0.0" 
PORT = 6060

class BattleShipServer:
    def __init__(self):
        self.clients = []
        self.player_data = {} 
        self.turn = 0 
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        player_index = -1
        with self.lock:
            player_index = len(self.clients)
            self.clients.append(conn)
        
        print(f"Oyuncu {player_index} bağlandı: {addr}")
        conn.send(f"PLAYER:{player_index}\n".encode())
        buffer = ""

        while True:
            try:
                data = conn.recv(4096).decode()
                if not data:
                    break

                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    print(f"Oyuncu {player_index} mesajı: {line}")
                    self.process_command(player_index, line)
                
            except Exception as e:
                print(f"Hata: {e}")
                break

        print(f"Bağlantı kesildi: {player_index} ({addr})")
        with self.lock:
            if conn in self.clients:
                self.clients.remove(conn)
        conn.close()

    def process_command(self, p_idx, data):
        # Oyuncu hazır olduğunda
        if data.startswith("READY:"):
            self.player_data[p_idx] = data.split(":")[1]
            print(f"Oyuncu {p_idx} hazır.")
            
            # İstemcinin 'ready_clicked' içindeki network.send() fonksiyonunun 
            # takılı kalmaması için hemen bir yanıt gönderiyoruz
            self.clients[p_idx].send("OK\n".encode())

            # İki oyuncu da hazırsa oyunu başlat
            if len(self.player_data) == 2:
                print("Her iki oyuncu hazır. Oyun başlıyor...")
                # Oyuncu 0'a senin sıran de
                self.clients[0].send("TURN:YES\n".encode())
                # Oyuncu 1'e bekle de
                self.clients[1].send("TURN:NO\n".encode())

        elif data.startswith("ATTACK:"):
            if p_idx == self.turn:
                target_idx = 1 if p_idx == 0 else 0
                # Saldırıyı diğer oyuncuya ilet
                self.clients[target_idx].send(f"{data}\n".encode())
                # Sırayı değiştir ve oyunculara yeni durumu bildir
                self.turn = target_idx
                self.clients[self.turn].send("TURN:YES\n".encode())
                self.clients[p_idx].send("TURN:NO\n".encode())

        elif data.startswith("RESULT:"):
            target_idx = 1 if p_idx == 0 else 0
            self.clients[target_idx].send(f"{data}\n".encode())

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode())
            except:
                pass

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Portun hızlıca tekrar kullanılabilmesi için
        server.bind((HOST, PORT))
        server.listen(2)
        print(f"Amiral Battı Sunucusu {PORT} portunda çalışıyor...")

        while True:
            conn, addr = server.accept()
            if len(self.clients) < 2:
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.start()
            else:
                conn.send("ERROR:Sunucu dolu\n".encode())
                conn.close()

if __name__ == "__main__":
    server = BattleShipServer()
    server.start()
