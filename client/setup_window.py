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
        self.orientation = "H"
        self.ship_sizes = [5, 4, 3, 3, 2]
        self.ship_names = ["Carrier", "Battleship", "Destroyer", "Submarine", "Patrol"]
        self.current_ship_index = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel(f"Hos geldin {self.username}. Gemilerini hazirla!")
        layout.addWidget(self.status_label)

        self.ships_count_label = QLabel(self.get_ship_progress_text())
        layout.addWidget(self.ships_count_label)

        self.current_ship_label = QLabel(self.get_current_ship_text())
        layout.addWidget(self.current_ship_label)

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
        self.ready_button.setEnabled(False)
        layout.addWidget(self.ready_button)

        self.setLayout(layout)

    def get_ship_progress_text(self):
        return f"Yerlestirilen: {self.current_ship_index}/5"

    def get_current_ship_text(self):
        if self.current_ship_index >= len(self.ship_sizes):
            return "Tum gemiler yerlestirildi."
        size = self.ship_sizes[self.current_ship_index]
        name = self.ship_names[self.current_ship_index]
        return f"Sıradaki gemi: {name} (Boyut {size})"

    def change_orientation(self, value):
        self.orientation = "H" if value == "Yatay" else "V"

    def place_ship_ui(self, x, y):
        if self.current_ship_index >= len(self.ship_sizes):
            QMessageBox.information(self, "Bilgi", "Tum gemiler yerlestirildi.")
            return

        size = self.ship_sizes[self.current_ship_index]
        success = place_ship(self.board, x, y, size, self.orientation)

        if success:
            self.current_ship_index += 1
            self.ships_count_label.setText(self.get_ship_progress_text())
            self.current_ship_label.setText(self.get_current_ship_text())
            self.update_board_visuals()
            if self.current_ship_index == len(self.ship_sizes):
                self.ready_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "Hata", "Gecersiz yerlesim!")

    def update_board_visuals(self):
        for i in range(10):
            for j in range(10):
                if self.board[i][j] == 1:
                    self.buttons[i][j].setStyleSheet(
                        "background-color: #2E86C1; border: 1px solid white;"
                    )
                else:
                    self.buttons[i][j].setStyleSheet("")

    def ready_clicked(self):
        if self.current_ship_index < len(self.ship_sizes):
            QMessageBox.warning(self, "Hata", "Lutfen tum gemileri yerlestirin!")
            return

        board_data = str(self.board)
        self.network.send(f"READY:{board_data}\n", wait_response=False)

        self.game_window = GameWindow(self.network, self.board)
        self.game_window.show()
        self.close()
