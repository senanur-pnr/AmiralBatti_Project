BOARD_SIZE = 10

def create_board():
    return [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

def print_board(board):
    for row in board:
        print(" ".join(str(cell) for cell in row))
    print()

def place_ship(board, x, y, size, orientation):
    # orientation: "H" or "V"
    if orientation == "H":
        if y + size > BOARD_SIZE:
            return False

        for i in range(size):
            if board[x][y + i] != 0:
                return False

        for i in range(size):
            board[x][y + i] = 1

    elif orientation == "V":
        if x + size > BOARD_SIZE:
            return False
        for i in range(size):
            if board[x + i][y] != 0:
                return False
        for i in range(size):
            board[x + i][y] = 1
    return True

def fire(board, x, y):
    if board[x][y] == 1:
        board[x][y] = 3  # hit
        return "hit"
    elif board[x][y] == 0:
        board[x][y] = 2  # miss
        return "miss"
    else:
        return "already"

def all_ships_sunk(board):
    for row in board:
        if 1 in row:
            return False
    return True