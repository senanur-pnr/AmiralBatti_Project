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
        for i in range(10):
            for j in range(10):
                if self.my_board[i][j] == SHIP:
                    self.my_buttons[i][j].setStyleSheet("background-color: blue;")

    def fire_at_enemy(self, x, y):
        if not self.my_turn:
            QMessageBox.warning(self, "Uyarı", "Sıra sizde değil!")
            return
        
        # Sunucuya saldırı komutu gönder[cite: 2]
        self.network.send(f"ATTACK:{x},{y}")

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
        """Sunucudan gelen komutları işler"""
        if data.startswith("PLAYER:"):
            self.my_role = data.split(":")[1]
            self.status_label.setText(f"Rolünüz: Oyuncu {self.my_role}")
            
        elif data.startswith("START:"):
            starter = data.split(":")[1]
            self.my_turn = (self.my_role == starter)
            status = "Sıra Sizde!" if self.my_turn else "Rakip Bekleniyor..."
            self.status_label.setText(status)

        elif data.startswith("ATTACK:"):
            # Rakip bana ateş etti
            coords = data.split(":")[1].split(",")
            x, y = int(coords[0]), int(coords[1])
            result = fire(self.my_board, x, y)
            
            # Sonucu hem kendimde güncelle hem sunucuya/rakibe gönder[cite: 2]
            color = "red" if result == "hit" else "gray"
            self.my_buttons[x][y].setStyleSheet(f"background-color: {color};")
            self.network.send(f"RESULT:{x},{y},{result}")
            
            if result == "miss":
                self.my_turn = True
                self.status_label.setText("Sıra Sizde!")

        elif data.startswith("RESULT:"):
            # Benim atışımın sonucu geldi
            parts = data.split(":")[1].split(",")
            x, y, res = int(parts[0]), int(parts[1]), parts[2]
            
            color = "red" if res == "hit" else "gray"
            self.enemy_buttons[x][y].setStyleSheet(f"background-color: {color};")
            self.enemy_buttons[x][y].setEnabled(False)
            
            if res == "miss":
                self.my_turn = False
                self.status_label.setText("Sıra Rakipte...")
            
            # Oyun bitti mi kontrolü sunucuya veya yerel board'a eklenebilir