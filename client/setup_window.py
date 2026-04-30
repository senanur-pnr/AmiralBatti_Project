import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QGridLayout, QVBoxLayout, QLabel, QComboBox, QMessageBox
)

from board import create_board, place_ship
from game_window import GameWindow

class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemi Yerleştirme")
        self.setGeometry(300, 200, 500, 550)

        self.board = create_board()
        self.selected_size = 3
        self.orientation = "H"

        self.placed_ships = 0
        self.max_ships = 5

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Gemilerini Yerleştir")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        info_label = QLabel("Gemi boyutu seç, yön seç ve tahtaya tıkla")
        layout.addWidget(info_label)

        self.ships_count_label = QLabel(
            f"Yerleştirilen gemi: {self.placed_ships}/{self.max_ships}"
        )
        layout.addWidget(self.ships_count_label)

        self.size_selector = QComboBox()
        self.size_selector.addItems(["1", "2", "3", "4"])
        self.size_selector.setCurrentText("3")
        self.size_selector.currentTextChanged.connect(self.change_size)
        layout.addWidget(self.size_selector)

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
                btn.clicked.connect(lambda _, x=i, y=j: self.place_ship_ui(x, y))
                self.grid_layout.addWidget(btn, i, j)
                row.append(btn)
            self.buttons.append(row)

        layout.addLayout(self.grid_layout)

        self.ready_button = QPushButton("Hazırım")
        self.ready_button.clicked.connect(self.ready_clicked)
        layout.addWidget(self.ready_button)

        self.setLayout(layout)

    def change_size(self, value):
        self.selected_size = int(value)

    def change_orientation(self, value):
        if value == "Yatay":
            self.orientation = "H"
        else:
            self.orientation = "V"

    def place_ship_ui(self, x, y):
        if self.placed_ships >= self.max_ships:
            QMessageBox.information(self, "Bilgi", "Tüm gemiler zaten yerleştirildi.")
            return

        success = place_ship(self.board, x, y, self.selected_size, self.orientation)

        if success:
            self.placed_ships += 1
            self.ships_count_label.setText(
                f"Yerleştirilen gemi: {self.placed_ships}/{self.max_ships}"
            )
            self.update_board()
        else:
            QMessageBox.warning(self, "Hata", "Gemi buraya yerleştirilemez.")

    def update_board(self):
        for i in range(10):
            for j in range(10):
                if self.board[i][j] == 1:
                    self.buttons[i][j].setStyleSheet("background-color: blue;")
                else:
                    self.buttons[i][j].setStyleSheet("")

    def ready_clicked(self):
        if self.placed_ships < self.max_ships:
            QMessageBox.warning(self, "Hata", "Tüm gemileri yerleştirmedin!")
        else:
            self.game_window = GameWindow(self.board)
            self.game_window.show()
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SetupWindow()
    window.show()
    sys.exit(app.exec_())