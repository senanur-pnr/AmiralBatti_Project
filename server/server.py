import ast
import socket
import threading
from collections import deque

HOST = "0.0.0.0"
PORT = 6060
BOARD_SIZE = 10
EMPTY = 0
SHIP = 1
MISS = 2
HIT = 3
EXPECTED_SHIP_SIZES = [2, 3, 3, 4, 5]


class BattleShipServer:
    def __init__(self):
        self.clients = {}  # player_id -> socket
        self.lock = threading.Lock()
        self.reset_game_state()

    def reset_game_state(self):
        self.boards = {}
        self.ready = set()
        self.turn = 0
        self.game_over = False
        self.winner = None
        self.loser = None

    def safe_send(self, player_id, message):
        conn = self.clients.get(player_id)
        if not conn:
            return
        try:
            conn.send(f"{message}\n".encode())
        except Exception:
            pass

    def broadcast(self, message):
        for player_id in list(self.clients.keys()):
            self.safe_send(player_id, message)

    def send_turn_state(self):
        for player_id in self.clients:
            is_turn = "YES" if player_id == self.turn else "NO"
            self.safe_send(player_id, f"TURN:{is_turn}")

    def validate_board(self, board):
        if not isinstance(board, list) or len(board) != BOARD_SIZE:
            return False

        for row in board:
            if not isinstance(row, list) or len(row) != BOARD_SIZE:
                return False
            for cell in row:
                if not isinstance(cell, int) or cell not in (EMPTY, SHIP):
                    return False

        visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        ship_sizes = []

        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if board[x][y] != SHIP or visited[x][y]:
                    continue

                q = deque([(x, y)])
                visited[x][y] = True
                component = []

                while q:
                    cx, cy = q.popleft()
                    component.append((cx, cy))
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            if not visited[nx][ny] and board[nx][ny] == SHIP:
                                visited[nx][ny] = True
                                q.append((nx, ny))

                rows = {r for r, _ in component}
                cols = {c for _, c in component}
                size = len(component)

                if len(rows) == 1:
                    ys = sorted(c for _, c in component)
                    if ys != list(range(ys[0], ys[0] + size)):
                        return False
                elif len(cols) == 1:
                    xs = sorted(r for r, _ in component)
                    if xs != list(range(xs[0], xs[0] + size)):
                        return False
                else:
                    return False

                ship_sizes.append(size)

        return sorted(ship_sizes) == EXPECTED_SHIP_SIZES

    def resolve_attack(self, attacker_id, x, y):
        defender_id = 1 if attacker_id == 0 else 0
        board = self.boards.get(defender_id)
        if board is None:
            return defender_id, "invalid"

        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            return defender_id, "invalid"

        cell = board[x][y]
        if cell == SHIP:
            board[x][y] = HIT
            return defender_id, "hit"
        if cell == EMPTY:
            board[x][y] = MISS
            return defender_id, "miss"
        return defender_id, "already"

    def all_ships_sunk(self, player_id):
        board = self.boards.get(player_id)
        if board is None:
            return False
        for row in board:
            if SHIP in row:
                return False
        return True

    def process_ready(self, player_id, payload):
        if player_id in self.ready:
            self.safe_send(player_id, "ERROR:ALREADY_READY")
            return

        try:
            board = ast.literal_eval(payload)
        except Exception:
            self.safe_send(player_id, "ERROR:INVALID_BOARD")
            return

        if not self.validate_board(board):
            self.safe_send(player_id, "ERROR:INVALID_BOARD")
            return

        self.boards[player_id] = board
        self.ready.add(player_id)
        self.safe_send(player_id, "READY_OK")
        if len(self.ready) == 2:
            self.turn = 0
            self.send_turn_state()

    def process_attack(self, attacker_id, payload):
        if self.game_over:
            self.safe_send(attacker_id, "ERROR:GAME_ALREADY_OVER")
            return

        if len(self.ready) < 2:
            self.safe_send(attacker_id, "ERROR:GAME_NOT_READY")
            return

        if attacker_id != self.turn:
            self.safe_send(attacker_id, "ERROR:NOT_YOUR_TURN")
            return

        try:
            x_str, y_str = payload.split(",", 1)
            x, y = int(x_str), int(y_str)
        except Exception:
            self.safe_send(attacker_id, "ERROR:INVALID_ATTACK")
            self.send_turn_state()
            return

        defender_id, result = self.resolve_attack(attacker_id, x, y)
        self.broadcast(f"SHOT_RESULT:{attacker_id},{defender_id},{x},{y},{result}")

        if result in ("hit", "miss"):
            self.turn = defender_id
        self.send_turn_state()

        if result == "hit" and self.all_ships_sunk(defender_id):
            self.game_over = True
            self.winner = attacker_id
            self.loser = defender_id
            self.broadcast(f"GAME_OVER:{self.winner},{self.loser}")

    def process_command(self, player_id, command):
        if command.startswith("READY:"):
            self.process_ready(player_id, command.split(":", 1)[1])
        elif command.startswith("ATTACK:"):
            self.process_attack(player_id, command.split(":", 1)[1])
        else:
            self.safe_send(player_id, "ERROR:UNKNOWN_COMMAND")

    def handle_client(self, conn, addr):
        with self.lock:
            if len(self.clients) >= 2:
                conn.send("ERROR:SERVER_FULL\n".encode())
                conn.close()
                return
            player_id = 0 if 0 not in self.clients else 1
            self.clients[player_id] = conn

        print(f"Oyuncu {player_id} baglandi: {addr}")
        self.safe_send(player_id, f"PLAYER:{player_id}")
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
                    with self.lock:
                        self.process_command(player_id, line)
            except Exception:
                break

        print(f"Baglanti kesildi: {player_id} ({addr})")
        with self.lock:
            if player_id in self.clients:
                del self.clients[player_id]
            # Bir oyuncu dusunce oyun durumunu temizleyip yeni eslesmeye hazirliyoruz.
            self.reset_game_state()
        conn.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(2)
        print(f"Amiral Batti Sunucusu {PORT} portunda calisiyor...")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    battle_server = BattleShipServer()
    battle_server.start()
