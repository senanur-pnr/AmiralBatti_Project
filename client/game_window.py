import threading
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, QObject
from board import fire


class GameSignaller(QObject):
    """Thread icinden arayuzu guvenli guncellemek icin sinyal mekanizmasi."""
    data_received = pyqtSignal(str)


class GameWindow(QWidget):
    def __init__(self, network, my_board):
        super().__init__()
        self.network = network
        self.my_board = my_board
        self.my_turn = False
        self.recv_buffer = ""

        self.setWindowTitle("Amiral Batti - Savas Alani")
        self.setGeometry(200, 100, 900, 500)

        self.signaller = GameSignaller()
        self.signaller.data_received.connect(self.handle_server_data)

        self.init_ui()
        self.start_receiving()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.status_label = QLabel("Sunucudan rol bekleniyor...")
        self.status_label.setStyleSheet("font-size: 16px; color: blue;")
        main_layout.addWidget(self.status_label)

        boards_layout = QHBoxLayout()
        self.my_buttons = self.create_grid(boards_layout, is_enemy=False)
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
                if self.my_board[i][j] == 1:
                    self.my_buttons[i][j].setStyleSheet(
                        "background-color: blue; border: 1px solid white;"
                    )
                else:
                    self.my_buttons[i][j].setStyleSheet("")

    def fire_at_enemy(self, x, y):
        if not self.my_turn:
            QMessageBox.warning(self, "Uyari", "Sira sizde degil!")
            return

        if not self.enemy_buttons[x][y].isEnabled():
            return

        try:
            self.network.send(f"ATTACK:{x},{y}\n", wait_response=False)
            self.my_turn = False
            self.status_label.setText("Atis yapildi, sonuc bekleniyor...")
        except Exception as e:
            print(f"Gonderim hatasi: {e}")

    def start_receiving(self):
        thread = threading.Thread(target=self.receive_thread, daemon=True)
        thread.start()

    def receive_thread(self):
        while True:
            try:
                data = self.network.client.recv(1024).decode()
                if not data:
                    break
                self.signaller.data_received.emit(data)
            except Exception:
                break

    def handle_server_data(self, chunk):
        self.recv_buffer += chunk
        while "\n" in self.recv_buffer:
            msg, self.recv_buffer = self.recv_buffer.split("\n", 1)
            msg = msg.strip()
            if msg:
                self.handle_server_message(msg)

    def handle_server_message(self, msg):
        if msg.startswith("TURN:"):
            turn_info = msg.split(":", 1)[1]
            self.my_turn = (turn_info == "YES")
            status = "SIRA SIZDE!" if self.my_turn else "SIRA RAKIPTE..."
            color = "green" if self.my_turn else "red"
            self.status_label.setText(status)
            self.status_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {color};"
            )

        elif msg.startswith("ATTACK:"):
            try:
                coords = msg.split(":", 1)[1].split(",")
                x, y = int(coords[0]), int(coords[1])
                result = fire(self.my_board, x, y)

                # Rakibin hamlesi kirmizi tonlarinda.
                bg_color = "#d32f2f" if result == "hit" else "#ef9a9a"
                text = "X" if result == "hit" else "O"

                self.my_buttons[x][y].setStyleSheet(
                    f"background-color: {bg_color}; color: white; border: 1px solid black;"
                )
                self.my_buttons[x][y].setText(text)
                self.my_buttons[x][y].setEnabled(False)

                self.network.send(f"RESULT:{x},{y},{result}\n", wait_response=False)
            except Exception as e:
                print(f"Saldiri isleme hatasi: {e}")

        elif msg.startswith("RESULT:"):
            try:
                parts = msg.split(":", 1)[1].split(",")
                x, y, res = int(parts[0]), int(parts[1]), parts[2]

                # Kendi hamlem rakibinkinden farkli renkte.
                bg_color = "#2e7d32" if res == "hit" else "#616161"
                text = "X" if res == "hit" else "O"

                self.enemy_buttons[x][y].setStyleSheet(
                    f"background-color: {bg_color}; color: white; border: 1px solid black;"
                )
                self.enemy_buttons[x][y].setText(text)
                self.enemy_buttons[x][y].setEnabled(False)
            except Exception as e:
                print(f"Sonuc isleme hatasi: {e}")
