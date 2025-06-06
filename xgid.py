# struct to represent a backgammon position.
# xgid constructor
class Board:
    def __init__(self, line):
        parts = line.split(':')
        self.board = parts[0][5:]
        self.cube = parts[1]
        self.cube_position = parts[2]
        self.turn = parts[3]
        self.dice = parts[4]
        self.score_bottom = int(parts[5])
        self.score_top = int(parts[6])
        self.crawford = parts[7]
        self.length = int(parts[8])
        self.max_cube = int(parts[9])

# public_function
def extract_xgid(xgid):
    return Board(xgid)

# convert board back to xgid
def board_to_line(full_board):
    txt = "XGID="
    txt += full_board.board
    txt += (':' + full_board.cube)
    txt += (':' + full_board.cube_position)
    txt += (':' + full_board.turn)
    txt += (':' + full_board.dice)
    txt += (':' + str(full_board.score_bottom))
    txt += (':' + str(full_board.score_top))
    txt += (':' + full_board.crawford)
    txt += (':' + str(full_board.length))
    txt += (':' + str(full_board.max_cube))
    return txt

def xgid_to_filename(line):
    line = line.replace("=", "Y")
    return line.replace(":", "Z")


# return the board struct of a swapped input
def swap_board(full_board):
    full_board.turn = '1'
    if full_board.cube_position == '-1': full_board.cube_position = '1'
    reversed_board = full_board.board[::-1]
    new_board = []
    for c in reversed_board:
        if ord(c) == 45:
            new_board.append('-')
        elif ord(c) < 96:
            new_board.append(chr(ord(c) + 32))
        else:
            new_board.append(chr(ord(c) - 32))
    full_board.board = "".join(new_board)
    print("new board", full_board.turn, full_board.board)
