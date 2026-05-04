import sys
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QVBoxLayout, 
    QLabel, QComboBox, QMessageBox
)
from board import create_board, place_ship 
from game_window import GameWindow

class SetupWindow(QWidget):
    def __init__(self, network, username): 
        super().__init__()
        self.network = network
        self.username = username
        
        self.setWindowTitle(f"Gemi Yerlestirme - {self.username}")
        self.setGeometry(300, 200, 500, 600)

        self.board = create_board()
        self.selected_size = 1
        self.orientation = "H"
        self.placed_ships = 0
        self.max_ships = 5 

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel(f"Hos geldin {self.username}. Gemilerini hazirla!")
        layout.addWidget(self.status_label)

        self.ships_count_label = QLabel(f"Yerlestirilen: {self.placed_ships}/{self.max_ships}")
        layout.addWidget(self.ships_count_label)

        layout.addWidget(QLabel("Gemi Boyutu Sec:"))
        self.size_selector = QComboBox()
        self.size_selector.addItems(["1", "2", "3", "4"])
        self.size_selector.currentTextChanged.connect(self.change_size)
        layout.addWidget(self.size_selector)

        layout.addWidget(QLabel("Yon Sec:"))
        self.orientation_selector = QComboBox()
        self.orientation_selector.addItems(["Yatay", "Dikey"])
        self.orientation_selector.currentTextChanged.connect(self.change_orientation)
        layout.addWidget(self.orientation_selector)

        self.grid_layout = QGridLayout()
        self.buttons = []
        for i in range(10):
            row = []
            for j in range(10):
                btn = QPushButton("")
                btn.setFixedSize(35, 35)
                btn.clicked.connect(lambda checked, x=i, y=j: self.place_ship_ui(x, y))
                self.grid_layout.addWidget(btn, i, j)
                row.append(btn)
            self.buttons.append(row)
        layout.addLayout(self.grid_layout)

        self.ready_button = QPushButton("Hazirim ve Sunucuya Gonder")
        self.ready_button.clicked.connect(self.ready_clicked)
        layout.addWidget(self.ready_button)

        self.setLayout(layout)

    def change_size(self, value):
        self.selected_size = int(value)

    def change_orientation(self, value):
        self.orientation = "H" if value == "Yatay" else "V"

    def place_ship_ui(self, x, y):
        if self.placed_ships >= self.max_ships:
            QMessageBox.information(self, "Bilgi", "Tum gemiler yerlestirildi.")
            return

        success = place_ship(self.board, x, y, self.selected_size, self.orientation)

        if success:
            self.placed_ships += 1
            self.ships_count_label.setText(f"Yerlestirilen: {self.placed_ships}/{self.max_ships}")
            self.update_board_visuals()
        else:
            QMessageBox.warning(self, "Hata", "Gecersiz yerlesim!")

    def update_board_visuals(self):
        for i in range(10):
            for j in range(10):
                if self.board[i][j] == 1:
                    self.buttons[i][j].setStyleSheet("background-color: #2E86C1; border: 1px solid white;")
                else:
                    self.buttons[i][j].setStyleSheet("")

    def ready_clicked(self):
        if self.placed_ships < self.max_ships:
            QMessageBox.warning(self, "Hata", "Lutfen tum gemileri yerlestirin!")
            return
        
        board_data = str(self.board)
        response = self.network.send(f"READY:{board_data}")
        
        if response:
            QMessageBox.information(self, "Basarili", "Gemiler sunucuya iletildi. Rakip bekleniyor...")
            self.game_window = GameWindow(self.network, self.board) 
            self.game_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Baglanti Hatasi", "Sunucuya veri gonderilemedi!")