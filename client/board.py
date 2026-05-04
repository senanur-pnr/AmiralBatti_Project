BOARD_SIZE = 10

# Hücre Durum Kodları (Okunabilirlik için sabitler ekledik)
EMPTY = 0
SHIP = 1
MISS = 2
HIT = 3

def create_board():
    """10x10'luk boş bir oyun tahtası oluşturur."""
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def place_ship(board, x, y, size, orientation):
    """
    Belirtilen koordinata gemi yerleştirir. 
    Çakışma ve sınır kontrolü yapar.
    """
    if size <= 0 or not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return False

    # Tahta sınırları dışına çıkıyor mu?
    if orientation == "H":
        if y + size > BOARD_SIZE:
            return False
        # Çakışma kontrolü
        for i in range(size):
            if board[x][y + i] != EMPTY:
                return False
        # Yerleştirme
        for i in range(size):
            board[x][y + i] = SHIP
            
    elif orientation == "V":
        if x + size > BOARD_SIZE:
            return False
        # Çakışma kontrolü
        for i in range(size):
            if board[x + i][y] != EMPTY:
                return False
        # Yerleştirme
        for i in range(size):
            board[x + i][y] = SHIP
    else:
        return False

    return True

def fire(board, x, y):
    """
    Atış işlemini gerçekleştirir ve sonucunu döner.
    """
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return "invalid"

    if board[x][y] == SHIP:
        board[x][y] = HIT
        return "hit"
    elif board[x][y] == EMPTY:
        board[x][y] = MISS
        return "miss"
    else:
        return "already" # Zaten ateş edilmiş (HIT veya MISS)

def all_ships_sunk(board):
    """Tahtada hiç canlı gemi parçası (1) kalıp kalmadığını kontrol eder.[cite: 2]"""
    for row in board:
        if SHIP in row:
            return False
    return True

def get_board_state(board, hide_ships=False):
    """
    Tahtanın durumunu sunucuya göndermek veya ekrana basmak için hazırlar.
    hide_ships=True ise gemilerin yerini (1) gizler (Rakip tahtası için).
    """
    display_board = []
    for row in board:
        new_row = []
        for cell in row:
            if hide_ships and cell == SHIP:
                new_row.append(EMPTY)
            else:
                new_row.append(cell)
        display_board.append(new_row)
    return display_board

def print_board(board):
    """Tahtayı terminalde okunabilir şekilde yazdırır."""
    symbols = {
        EMPTY: ".",
        SHIP: "S",
        MISS: "O",
        HIT: "X",
    }
    for row in board:
        print(" ".join(symbols.get(cell, "?") for cell in row))
