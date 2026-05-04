import threading
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, QObject


class GameSignaller(QObject):
    data_received = pyqtSignal(str)


class GameWindow(QWidget):
    def __init__(self, network, my_board):
        super().__init__()
        self.network = network
        self.my_board = my_board
        self.my_turn = False
        self.game_over = False
        self.recv_buffer = ""
        self.pending_attacks = set()
        self.player_id = self.network.player_id

        self.setWindowTitle("Amiral Batti - Savas Alani")
        self.setGeometry(200, 100, 900, 500)

        self.signaller = GameSignaller()
        self.signaller.data_received.connect(self.handle_server_data)

        self.init_ui()
        self.start_receiving()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.status_label = QLabel("Rakip bekleniyor...")
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
        if self.game_over:
            return
        if not self.my_turn:
            QMessageBox.warning(self, "Uyari", "Sira sizde degil!")
            return
        if not self.enemy_buttons[x][y].isEnabled():
            return
        if (x, y) in self.pending_attacks:
            return

        self.pending_attacks.add((x, y))
        try:
            self.network.send(f"ATTACK:{x},{y}\n", wait_response=False)
            self.status_label.setText("Atis gonderildi, sunucu sonucu bekleniyor...")
        except Exception as e:
            self.pending_attacks.discard((x, y))
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

    def disable_all_grids(self):
        for i in range(10):
            for j in range(10):
                self.my_buttons[i][j].setEnabled(False)
                self.enemy_buttons[i][j].setEnabled(False)

    def handle_server_message(self, msg):
        if msg.startswith("TURN:"):
            turn_info = msg.split(":", 1)[1]
            self.my_turn = (turn_info == "YES") and (not self.game_over)
            status = "SIRA SIZDE!" if self.my_turn else "SIRA RAKIPTE..."
            color = "green" if self.my_turn else "red"
            self.status_label.setText(status)
            self.status_label.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {color};"
            )
            return

        if msg.startswith("SHOT_RESULT:"):
            try:
                payload = msg.split(":", 1)[1]
                attacker, defender, x, y, result = payload.split(",")
                attacker = int(attacker)
                defender = int(defender)
                x = int(x)
                y = int(y)
            except Exception:
                return

            if attacker == self.player_id:
                self.pending_attacks.discard((x, y))
                if result == "hit":
                    self.enemy_buttons[x][y].setStyleSheet(
                        "background-color: #2e7d32; color: white; border: 1px solid black;"
                    )
                    self.enemy_buttons[x][y].setText("X")
                    self.enemy_buttons[x][y].setEnabled(False)
                elif result == "miss":
                    self.enemy_buttons[x][y].setStyleSheet(
                        "background-color: #616161; color: white; border: 1px solid black;"
                    )
                    self.enemy_buttons[x][y].setText("O")
                    self.enemy_buttons[x][y].setEnabled(False)
                elif result in ("already", "invalid"):
                    self.status_label.setText("Gecersiz/tekrar atis. Tekrar deneyin.")

            if defender == self.player_id:
                if result == "hit":
                    self.my_buttons[x][y].setStyleSheet(
                        "background-color: #d32f2f; color: white; border: 1px solid black;"
                    )
                    self.my_buttons[x][y].setText("X")
                    self.my_buttons[x][y].setEnabled(False)
                elif result == "miss":
                    self.my_buttons[x][y].setStyleSheet(
                        "background-color: #ef9a9a; color: white; border: 1px solid black;"
                    )
                    self.my_buttons[x][y].setText("O")
                    self.my_buttons[x][y].setEnabled(False)
            return

        if msg.startswith("GAME_OVER:"):
            try:
                payload = msg.split(":", 1)[1]
                winner, loser = payload.split(",")
                winner = int(winner)
                loser = int(loser)
            except Exception:
                return

            self.game_over = True
            self.my_turn = False
            self.pending_attacks.clear()
            self.disable_all_grids()

            if self.player_id == winner:
                self.status_label.setText("OYUN BITTI - KAZANDINIZ!")
                QMessageBox.information(self, "Oyun Bitti", "Tebrikler, kazandiniz!")
            elif self.player_id == loser:
                self.status_label.setText("OYUN BITTI - KAYBETTINIZ!")
                QMessageBox.information(self, "Oyun Bitti", "Tum gemileriniz batirildi.")
            else:
                self.status_label.setText("OYUN BITTI")
            return

        if msg.startswith("ERROR:"):
            reason = msg.split(":", 1)[1]
            if reason == "INVALID_BOARD":
                QMessageBox.critical(self, "Hata", "Sunucu gemi dizilimini gecersiz buldu.")
                self.game_over = True
                self.disable_all_grids()
                self.status_label.setText("GECERSIZ TAHTA")
            elif reason == "NOT_YOUR_TURN":
                QMessageBox.warning(self, "Uyari", "Sira sizde degil!")
            elif reason == "GAME_ALREADY_OVER":
                self.game_over = True
                self.disable_all_grids()
                self.status_label.setText("OYUN BITTI")
            elif reason == "INVALID_ATTACK":
                QMessageBox.warning(self, "Uyari", "Gecersiz saldiri komutu.")
            elif reason == "GAME_NOT_READY":
                QMessageBox.warning(self, "Bilgi", "Rakip henuz hazir degil.")
            elif reason == "UNKNOWN_COMMAND":
                QMessageBox.warning(self, "Uyari", "Bilinmeyen komut.")
