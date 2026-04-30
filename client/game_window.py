import sys
import threading

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout, QLabel
)

from board import create_board, fire
from network import Network

class GameWindow(QWidget):
    def __init__(self, my_board):
        super().__init__()
        self.setWindowTitle("Amiral Battı - Oyun")
        self.setGeometry(200, 100, 800, 500)

        self.my_board = my_board
        self.enemy_board = create_board()

        self.network = Network("127.0.0.1", 6060)

        self.init_ui()

        thread = threading.Thread(target=self.receive_data)
        thread.daemon = True
        thread.start()
        self.my_role = None  # "PLAYER:0" veya "PLAYER:1"
        self.my_turn = False

    def init_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Oyun Ekranı")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        boards_layout = QHBoxLayout()

        self.my_grid = QGridLayout()
        self.my_buttons = []

        for i in range(10):
            row = []
            for j in range(10):
                btn = QPushButton("")
                btn.setFixedSize(30, 30)
                self.my_grid.addWidget(btn, i, j)
                row.append(btn)
            self.my_buttons.append(row)

        self.enemy_grid = QGridLayout()
        self.enemy_buttons = []

        for i in range(10):
            row = []
            for j in range(10):
                btn = QPushButton("")
                btn.setFixedSize(30, 30)
                btn.clicked.connect(lambda _, x=i, y=j: self.fire_enemy(x, y))
                self.enemy_grid.addWidget(btn, i, j)
                row.append(btn)
            self.enemy_buttons.append(row)

        self.update_my_board()

        boards_layout.addLayout(self.my_grid)
        boards_layout.addLayout(self.enemy_grid)

        main_layout.addLayout(boards_layout)
        self.setLayout(main_layout)

    def update_my_board(self):
        for i in range(10):
            for j in range(10):
                if self.my_board[i][j] == 1:
                    self.my_buttons[i][j].setStyleSheet("background-color: blue;")

    def fire_enemy(self, x, y):
        if not self.my_turn:
            print("Sıra sizde değil, rakibi bekleyin!")
            return
        
        self.network.send(f"{x},{y}")

        result = fire(self.enemy_board, x, y)

        if result == "hit":
            self.enemy_buttons[x][y].setStyleSheet("background-color: red;")
        elif result == "miss":
            self.enemy_buttons[x][y].setStyleSheet("background-color: gray;")
            self.enemy_buttons[x][y].setStyleSheet("background-color: gray;")
            self.my_turn = False
        if result != "hit":
            self.my_turn = False
            
    def receive_data(self):
        while True:
            try:
                data = self.network.client.recv(1024).decode()
                if data:
                    if data.startswith("PLAYER:"):
                    # Rol ataması: PLAYER:0 ise ilk oyuncudur ve sıra ondadır
                        self.my_role = data
                        if data == "PLAYER:0":
                            self.my_turn = True
                            print("Oyuna siz başlıyorsunuz!")
                        else:
                            self.my_turn = False
                            print("Rakibin başlaması bekleniyor...")
                
                    elif "," in data:
                    # Rakipten gelen atış koordinatı
                        x, y = map(int, data.split(","))
                        self.update_from_enemy(x, y)
                        self.my_turn = True # Rakip ateş etti, sıra bana geçti
            
            except:
                break

    def update_from_enemy(self, x, y):
        result = fire(self.my_board, x, y)

        if result == "hit":
            self.my_buttons[x][y].setStyleSheet("background-color: red;")
        elif result == "miss":
            self.my_buttons[x][y].setStyleSheet("background-color: gray;")
        else:
            print("Rakip zaten buraya ateş etmiş")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    sample_board = create_board()
    sample_board[0][0] = 1
    sample_board[0][1] = 1
    sample_board[2][2] = 1

    window = GameWindow(sample_board)
    window.show()
    sys.exit(app.exec_())