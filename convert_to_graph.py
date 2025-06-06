import os
import sys
import xgid

class Position:
    def __init__(self, line, is_cube, stage):
        full_board = xgid.extract_xgid(line)
        if full_board.turn == '-1':
            xgid.swap_board(full_board)
        
        self.xgid = xgid.board_to_line(full_board) #string
        self.is_cube = is_cube #boolean
        self.stage = stage #string
        self.categories = [] #list(string)

    def print_pos(self):
        print(self.xgid, "isCube =", self.is_cube, "Stage = ", self.stage)
        for cat in self.categories:
            print("\t", cat)

class Filter:
    def __init__(self, is_cube, stage, line):
        self.is_cube = is_cube
        self.stage = stage
        if (len(line) > 0): self.inner = Filter_Recursive(line, 0)
        else: self.inner = None

    def print_fil(self):
        print("is_cube =", self.is_cube, "stage =", self.stage)
        if self.inner: self.inner.print_fil_rec(0)

class Filter_Recursive:
    def __init__(self, line, depth):
        print("line = ", line)
        self.left = None #Filter
        self.right = None #Filter
        self.category = None #string
        self.injunction = None #string (AND; OR; NONE)
        self.populate_filter(line, depth)

    # parse boolean statement into a filter
    def populate_filter(self, line, depth):
        if len(line) == 1: 
            self.category = line[0]
            self.injunction = "NONE"
            return

        # left branch
        index = 0
        if line[index] == "(":
            print("parenth", depth)
            while line[index] != ")":
                index += 1
            if index == len(line) - 1:
                self.populate_filter(line[1:-1], depth)
                return
            self.left = Filter_Recursive(line[1:index], depth+1)
            index += 1
        else:
            print("regular", depth)
            self.left = Filter_Recursive(line[index:1], depth+1)
            index = 1

        # injunction
        print("index inj = ", index, line, depth)
        self.injunction = line[index]
        print("injunction = ", self.injunction, depth)
        index += 1

        # right branch
        print("index = ", index, depth)
        self.right = Filter_Recursive(line[index:], depth+1)


    def print_fil_rec(self, depth):
        tabs = depth * '\t'
        if self.injunction == "NONE":
            print(tabs + self.category)
        elif self.injunction == "AND":
            print(tabs + "AND")
            self.left.print_fil_rec(depth + 1)
            self.right.print_fil_rec(depth + 1)
        elif self.injunction == "OR":
            print(tabs + "OR")
            self.left.print_fil_rec(depth + 1)
            self.right.print_fil_rec(depth + 1)


# string -> boolean
# extracts information from xgid on whether or not to cube
def get_is_cube(line):
    full_board = xgid.extract_xgid(line)
    return (full_board.dice == '00')

# string -> Position
# takes lines from position file input and populates an instance of a Position class
def process_file(file_path):
    with open(file_path, "r", encoding="unicode_escape") as f:
        lines = f.read().split('\n')
        lines.pop()
        print(lines, file_path)
        position = Position(line=lines[0], is_cube=get_is_cube(lines[0]), stage=lines[1])
        categories = [] #list(string)
        for i in range(2, len(lines)):
            categories.append(lines[i][1:])
        print("CATEGIROES", categories)
        position.categories = categories

    position.print_pos()
    return position

# string -> Filter
# takes lines from filter file input and populates an instance of a Filter class
def process_filter(file_path):
    with open(file_path, "r", encoding="unicode_escape") as f:
        lines = f.read().split('\n')
        lines.pop()
        print("LINES", lines)
        if len(lines) <= 1:
            return Filter(lines[0] == "Cube", None, [])
        strand = ""
        for line in lines[2:]: strand += (line + ' ')
        strand_list = strand.split(' ')
        strand_list.pop()
        print(strand)
        print(lines)
        filter = Filter(lines[0] == "Cube", lines[1], strand_list)
        print("FILTER", filter.print_fil())
        return filter

# public function that converts lines from input function to structs
# that the filter function can process
def get(file_path, isFile):
    if isFile: return process_file(file_path)
    else: return process_filter(file_path)
