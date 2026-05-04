import threading
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QVBoxLayout, 
    QHBoxLayout, QLabel, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, QObject
from board import fire, all_ships_sunk, SHIP, HIT, MISS

class GameSignaller(QObject):
    """Thread içinden arayüzü güvenli güncellemek için sinyal mekanizması"""
    data_received = pyqtSignal(str)

class GameWindow(QWidget):
    def __init__(self, network, my_board):
        super().__init__()
        self.network = network # SetupWindow'dan gelen network nesnesi
        self.my_board = my_board
        self.my_turn = False
        self.my_role = None

        self.setWindowTitle("Amiral Battı - Savaş Alanı")
        self.setGeometry(200, 100, 900, 500)
        
        self.signaller = GameSignaller()
        self.signaller.data_received.connect(self.handle_server_message)

        self.init_ui()
        self.start_receiving()

    def render_my_ships(self):
        """Kendi tahtamdaki gemileri maviye boyar"""
        for i in range(10):
            for j in range(10):
                # SHIP veya 1 değerini kontrol et
                if self.my_board[i][j] == 1: 
                    self.my_buttons[i][j].setStyleSheet("background-color: blue; border: 1px solid white;")   

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.status_label = QLabel("Sunucudan rol bekleniyor...")
        self.status_label.setStyleSheet("font-size: 16px; color: blue;")
        main_layout.addWidget(self.status_label)

        boards_layout = QHBoxLayout()
        
        # Kendi Tahtam (Sol)
        self.my_buttons = self.create_grid(boards_layout, is_enemy=False)
        # Rakip Tahtası (Sağ)
        self.enemy_buttons = self.create_grid(boards_layout, is_enemy=True)

        main_layout.addLayout(boards_layout)
        self.setLayout(main_layout)
        self.render_my_ships()

    def create_grid(self, parent_layout, is_enemy):
        grid = QGridLayout()
        buttons = []
        for i in range(10):
            row = []
            for j in range(10):
                btn = QPushButton("")
                btn.setFixedSize(35, 35)
                if is_enemy:
                    btn.clicked.connect(lambda _, r=i, c=j: self.fire_at_enemy(r, c))
                grid.addWidget(btn, i, j)
                row.append(btn)
            buttons.append(row)
        parent_layout.addLayout(grid)
        return buttons

    def render_my_ships(self):
    # SHIP değerinin ne olduğunu görmek için test amaçlı yazdırabilirsin
    # print(f"Gelen Tahta: {self.my_board}") 
     for i in range(10):
        for j in range(10):
            # Gemiler tahtada genellikle 1 ile temsil edilir
            if self.my_board[i][j] == 1: 
                self.my_buttons[i][j].setStyleSheet("background-color: blue; border: 1px solid white;")
            else:
                self.my_buttons[i][j].setStyleSheet("")

    def fire_at_enemy(self, x, y):
        if not self.my_turn:
            QMessageBox.warning(self, "Uyarı", "Sıra sizde değil!")
            return
        
        # Sadece gönderiyoruz, yanıtı receive_thread içinde bekleyeceğiz
        try:
            self.network.client.send(f"ATTACK:{x},{y}".encode())
            # Gönderdikten sonra hemen donmayı engellemek için geçici olarak sırayı kapatabilirsin
            self.my_turn = False 
            self.status_label.setText("Atış yapıldı, yanıt bekleniyor...")
        except Exception as e:
            print(f"Gönderim hatası: {e}")

    def start_receiving(self):
        thread = threading.Thread(target=self.receive_thread, daemon=True)
        thread.start()

    def receive_thread(self):
        while True:
            try:
                data = self.network.client.recv(1024).decode()
                if data:
                    self.signaller.data_received.emit(data)
            except:
                break

    def handle_server_message(self, data):
        """Sunucudan gelen komutları işler ve ekranları renklendirir"""
        # Paketlerin yapışmasını önlemek için satır bazlı ayırıyoruz
        messages = data.strip().split("\n")
        
        for msg in messages:
            if not msg: continue
            print(f"İşlenen Komut: {msg}")

            # --- SIRA GÜNCELLEME ---
            if msg.startswith("TURN:"):
                turn_info = msg.split(":")[1]
                self.my_turn = (turn_info == "YES")
                status = "SIRA SİZDE!" if self.my_turn else "SIRA RAKİPTE..."
                color = "green" if self.my_turn else "red"
                self.status_label.setText(status)
                self.status_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

            # --- RAKİP BANA ATEŞ ETTİĞİNDE (Sol Tahta - Benim Alanım) ---
            elif msg.startswith("ATTACK:"):
                try:
                    coords = msg.split(":")[1].split(",")
                    x, y = int(coords[0]), int(coords[1])
                    from board import fire
                    result = fire(self.my_board, x, y)
                    
                    # Eğer gemim vurulduysa KIRMIZI, karavana ise AÇIK GRİ
                    bg_color = "red" if result == "hit" else "lightgray"
                    text = "X" if result == "hit" else "O"
                    
                    self.my_buttons[x][y].setStyleSheet(f"background-color: {bg_color}; color: white; border: 1px solid black;")
                    self.my_buttons[x][y].setText(text)
                    
                    # Sonucu sunucuya bildir (Sunucu bunu rakibe RESULT olarak iletir)
                    self.network.send(f"RESULT:{x},{y},{result}\n")
                except Exception as e:
                    print(f"Saldırı işleme hatası: {e}")

            # --- BEN RAKİBİ VURDUĞUMDA (Sağ Tahta - Rakip Alanı) ---
            elif msg.startswith("RESULT:"):
                try:
                    parts = msg.split(":")[1].split(",")
                    x, y, res = int(parts[0]), int(parts[1]), parts[2]
                
                    # İisabet varsa KIRMIZI, karavana ise KOYU GRİ
                    bg_color = "red" if res == "hit" else "gray"
                    text = "X" if res == "hit" else "O"
                    
                    self.enemy_buttons[x][y].setStyleSheet(f"background-color: {bg_color}; color: white; border: 1px solid black;")
                    self.enemy_buttons[x][y].setText(text)
                    self.enemy_buttons[x][y].setEnabled(False) # Aynı yere tekrar basılmasın

                    if res == "hit":
                        self.status_label.setText("MÜKEMMEL ATIŞ! Tekrar ateş edin.")
                        self.my_turn = True # İsabet halinde sıra oyuncuda kalır
                
                except Exception as e:
                    print(f"Sonuç işleme hatası: {e}")