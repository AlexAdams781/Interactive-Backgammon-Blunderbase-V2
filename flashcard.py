import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from pathlib import Path
import sys
import pickle
import eval
import xgid
import re
import copy
import queue
from threading import Thread
from collections import Counter
import pyperclip
import shutil
import random

root_dir = r"\Users\aadam\Documents\blunderbase\\"

myfont = ("Arial", 18)
mysmallfont = ("Arial", 12)
mymicrofont = ("Arial", 8)

marg = (50, 75)
# board dimensions are (600, 560)
board_dims = (600, 560)
canvas_dims = (700, 660)

analysis_done = set()

num_positions = 0
worker = None

def get_analysis(xgid_line):
    while True:
        if xgid_line in analysis_done:
            break

    print("Getting analysis for xgid =", xgid)
    with open(root_dir + r"cache//" + xgid.xgid_to_filename(xgid_line), 'rb') as f:
        return pickle.load(f)
    return None

class Move:
    def __init__(self, move):
        split_move = move.split('/')
        self.pos = []
        self.mult = 1
        is_capture = False
        print("Split", split_move)
        for elem in split_move:
            if elem == "bar":
                self.pos.append(25)
                continue
            if elem == "off":
                self.pos.append(0)
                continue

            index = 0
            while index < len(elem):
                if elem[index] == '*':
                    self.pos.append(int(elem[:index]))
                    is_capture = True
                    break
                if elem[index] == '(':
                    self.pos.append(int(elem[:index]))
                    self.mult = int(elem[index+1])
                    break
                index += 1
            if index == len(elem): self.pos.append(int(elem))

        self.cat = self.categorize(is_capture)

    def categorize(self, is_capture):
        if len(self.pos) == 3:
            return "pick_pass"
        elif is_capture:
            return "capture"
        elif self.mult > 1:
            return "double"
        else:
            return "regular"

def configure_canvases(canvas_1, canvas_2):
    canvas_1.white_pip_count = None
    canvas_2.white_pip_count = None
    canvas_1.black_pip_count = None
    canvas_2.black_pip_count = None
    canvas_1.position_counter = None
    canvas_2.position_counter = None
    canvas_1.stats = None
    canvas_2.stats = None

class App:
    def __init__(self, root):
        self.root = root
        self.current_index = -1
        self.current_canvas = None
        self.analysis = False
        self.canvases = {}
        self.xgid_map = {}

        self.correct = 0
        self.mistakes = 0
        self.blunders = 0

        root.bind("<Right>", self.switch_right)
        root.bind("<Up>", self.switch_up)
        root.bind("<Down>", self.switch_down)
        root.focus_set()

    def create_intro(self):
        canvas = tk.Canvas(self.root, width=canvas_dims[0], height=canvas_dims[1], bg="black")
        self.current_index += 1
        self.canvases[self.current_index] = (canvas, None)
        self.current_canvas = canvas

        canvas.create_text(canvas_dims[0]//2, 200, text="Blunderbase Flashcards", font=("Arial", 36), fill='white')
        start_btn = canvas.create_rectangle(canvas_dims[0]//2 - 50, 500, canvas_dims[0]//2 + 50, 560, fill='white')
        start_txt = canvas.create_text(canvas_dims[0]//2, 530, text='Start', font=myfont, fill='black')
        canvas.tag_bind(start_btn, "<Button-1>", lambda k : self.switch_right(None))
        canvas.tag_bind(start_txt, "<Button-1>", lambda k : self.switch_right(None))

    def create_outro(self):
        global num_positions

        canvas = tk.Canvas(self.root, width=canvas_dims[0], height=canvas_dims[1], bg="black")
        self.canvases[num_positions + 1] = (canvas, None)

        play_again_btn = canvas.create_rectangle(canvas_dims[0]//2 - 80, 280, canvas_dims[0]//2 + 80, 320, fill='white')
        play_again_txt = canvas.create_text(canvas_dims[0]//2, 300, text='Play Again', font=myfont, fill="black")
        canvas.tag_bind(play_again_btn, "<Button-1>", lambda k : restart_fn("play again"))
        canvas.tag_bind(play_again_txt, "<Button-1>", lambda k : restart_fn("play again"))

        exit_btn = canvas.create_rectangle(615, 10, 675, 40, fill='white')
        exit_txt = canvas.create_text(645, 25, text="Exit", fill='black')
        canvas.tag_bind(exit_btn, "<Button-1>", lambda k : exit_fn())
        canvas.tag_bind(exit_txt, "<Button-1>", lambda k : exit_fn())

        if self.mistakes == 0 and self.blunders == 0:
            canvas.create_text(canvas_dims[0]//2, 200, text='Nice Job!', font=("Arial", 36), fill='white')

        elif self.blunders > 0 and self.mistakes == 0:
            play_again_blunders_btn = canvas.create_rectangle(canvas_dims[0]//2 - 120, 340, canvas_dims[0]//2 + 120, 380, fill='white')
            play_again_blunders_txt = canvas.create_text(canvas_dims[0]//2, 360, text='Review Only Blunders', font=mysmallfont, fill="black")
            canvas.tag_bind(play_again_blunders_btn, "<Button-1>", lambda k : restart_fn("blunders"))
            canvas.tag_bind(play_again_blunders_txt, "<Button-1>", lambda k : restart_fn("blunders"))

        elif self.mistakes > 0:
            play_again_mistakes_btn = canvas.create_rectangle(canvas_dims[0]//2 - 120, 340, canvas_dims[0]//2 + 120, 380, fill='white')
            play_again_mistakes_txt = canvas.create_text(canvas_dims[0]//2, 360, text='Review Mistakes & Blunders', font=mysmallfont, fill="black")
            canvas.tag_bind(play_again_mistakes_btn, "<Button-1>", lambda k : restart_fn("mistakes"))
            canvas.tag_bind(play_again_mistakes_txt, "<Button-1>", lambda k : restart_fn("mistakes"))

            if self.blunders > 0:
                play_again_blunders_btn = canvas.create_rectangle(canvas_dims[0]//2 - 120, 400, canvas_dims[0]//2 + 120, 440, fill='white')
                play_again_blunders_txt = canvas.create_text(canvas_dims[0]//2, 420, text='Review Only Blunders', font=mysmallfont, fill="black")
                canvas.tag_bind(play_again_blunders_btn, "<Button-1>", lambda k : restart_fn("blunders"))
                canvas.tag_bind(play_again_blunders_txt, "<Button-1>", lambda k : restart_fn("blunders"))

        print("STATS", self.correct, self.mistakes, self.blunders)
        canvas.stats = canvas.create_text(canvas_dims[0] // 2, canvas_dims[1] - 40, \
            text="Correct: " + str(self.correct) + "\tMistake: " + str(self.mistakes) + "\tBlunders: " + str(self.blunders), \
            font=myfont, fill='white')

    def create_canvas(self, xgid, file_path):
        canvas_1 = tk.Canvas(self.root, width=canvas_dims[0], height=canvas_dims[1], bg="black")
        canvas_2 = tk.Canvas(self.root, width=canvas_dims[0], height=canvas_dims[1], bg="black")
        configure_canvases(canvas_1, canvas_2)

        self.current_index += 1
        self.canvases[self.current_index] = (canvas_1, canvas_2)
        self.current_canvas = canvas_1
        self.xgid_map[self.current_index] = (xgid, file_path)
        configure_board(canvas_1, Board(xgid, file_path))
        print(len(self.canvases))
        print(self.current_index)
        print(xgid)

    def show_canvas(self, boardinfo=None):
        global num_positions

        self.current_canvas.pack_forget()
        print("forget index", self.current_index, num_positions)
        if self.current_index == 0:
            self.current_canvas = self.canvases[self.current_index][0]
            self.current_canvas.pack()
            return

        if self.current_index == num_positions + 1:
            print("Creating outro")
            self.create_outro()
            self.current_canvas = self.canvases[self.current_index][0]
            self.current_canvas.pack()
            return

        xgid, file_path = self.xgid_map[self.current_index]
        if not boardinfo: boardinfo = Board(xgid, file_path)
        if self.analysis: 
            print("show analysis")
            self.current_canvas = self.canvases[self.current_index][1]
            configure_board(self.current_canvas, boardinfo, analysis=get_analysis(xgid))
        else:
            self.current_canvas = self.canvases[self.current_index][0]
            configure_board(self.current_canvas, boardinfo)
        self.current_canvas.pack()

    def switch_right(self, event):
        global num_positions

        print("right")
        if self.current_index == 0 or self.current_index == num_positions:
            self.current_index += 1
            self.show_canvas()
            return

        if self.analysis == False:
            # run the review and add to priority queue
            xgid = self.xgid_map[self.current_index]
            self.current_index += 1
            self.show_canvas()
            print(len(self.canvases))
            print(self.current_index)

    def switch_up(self, event):
        self.analysis = True
        self.show_canvas()

    def switch_down(self, event):
        self.analysis = False
        self.show_canvas()

    def incr_stats(self, category):
        if category == "correct":
            self.correct += 1
        elif category == "mistake":
            self.mistakes += 1
        else:
            self.blunders += 1
        print("STATS", self.correct, self.mistakes, self.blunders)

root = tk.Tk()
root.attributes('-fullscreen', True)
app = App(root)

def get_dice_image(d):
    print(d)
    if d == 1:
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_1.png')
    elif d == 2:
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_2.png')
    elif d == 3:
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_3.png') 
    elif d == 4:
        print("here")
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_4.png')
    elif d == 5:
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_5.png')
    elif d == 6:
        image = Image.open(r'C:\Users\aadam\Documents\Blunderbase\Graphics\Dice_6.png')
    photo = image.resize((30,30), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(photo)
    return photo

def moveLength(move):
    index = move.find('(')
    if index != -1:
        mult = int(move[index+1])
    else:
        mult = 1
    print(move, mult)

    move_split = re.split(r'[*(/]', move)
    print(move_split)
    if move_split[0] == 'bar':
        old_pos = 25
    else:
        old_pos = int(move_split[0])
    if move_split[1] == 'off':
        new_pos = 0
    else:
        new_pos = int(move_split[1])
    return mult * (old_pos - new_pos)

def getMoves(line):
    move_list = []
    for elem in line.split(' '):
        print("elem", elem)
        if elem != '' and not elem.startswith('-') and not elem.startswith('+'):
            move_list.append(elem)
        else: break
    return move_list

def is_bearoff(move):
    return move.find("off") != -1

def getNumMoves(xgid, dice, checkers_home):
    if dice[0] != dice[1]:
        dicesum = dice[0] + dice[1]
        num_dice = 2
    else:
        dicesum = 4 * dice[0]
        num_dice = 4

    analysis = get_analysis(xgid)
    move_list = getMoves(analysis[0][0])

    print(analysis, move_list)
    movesum = 0
    bearoff = False
    for move in move_list:
        movesum += moveLength(move)
        if is_bearoff(move): bearoff = True

    print("dicesum", num_dice, dicesum, movesum)
    if is_bearoff:
        return (min(num_dice, 15 - checkers_home), None)
    if dicesum == movesum:
        return (num_dice, None)
    elif num_dice == 2:
        return (1, movesum)
    return (movesum // dice[0], movesum)


class Board:
    def __init__(self, xgid, file_path):
        print("XGID!", xgid)
        parts = xgid.split(':')
        board = parts[0][5:]
        cube = parts[1]
        cube_position = parts[2]
        turn = parts[3]
        dice = parts[4]
        score_bottom = parts[5]
        score_top = parts[6]
        crawford = parts[7]
        length = parts[8]
        max_cube = parts[9]

        self.white_home, self.black_home = 15, 15
        self.xgid = xgid
        self.board = [0] * 24
        self.black_pip_count, self.white_pip_count = 0, 0
        for i, c in enumerate(board[1:-1]):
            if ord(c) == 45:
                # blank
                self.board[i] = 0
            elif ord(c) < 80:
                # white
                self.board[i] = ord(c) - 64
                self.white_home -= self.board[i]
                self.white_pip_count += ((i+1) * self.board[i])
            else:
                # black
                self.board[i] = 96 - ord(c)
                self.black_home += self.board[i]
                self.black_pip_count += ((24-i) * (-self.board[i]))
        print("BOARD:", board)

        if board[-1] == '-': self.white_bar = 0
        else:
            # white
            self.white_bar = ord(board[-1]) - 64
            self.white_home -= self.white_bar
        if board[0] == '-': self.black_bar = 0
        else:
            self.black_bar = ord(board[0]) - 96
            self.black_home -= self.black_bar
        self.white_pip_count += (25 * self.white_bar)
        self.black_pip_count += (25 * self.black_bar)

        if cube == '0': self.cube = '64'
        else: self.cube = str(2**int(cube))
        self.cube_pos = int(cube_position)
        self.dice = (int(dice[0]), int(dice[1]))
        if dice == '00': self.isCube = True
        else: 
            self.isCube = False
            self.dice1 = get_dice_image(self.dice[0])
            self.dice2 = get_dice_image(self.dice[1])

        self.isDouble = False
        self.isRoll = False
        self.isTake = False
        self.isPass = False
        self.movelog = [] # list((int, int))

        self.score_bot = score_bottom
        self.score_top = score_top
        if crawford == '1': self.crawford = True
        else: self.crawford = False

        self.length = length
        self.file_path = file_path
        print("finished:")

def place_checkers(canvas, boardinfo, pos, num, color):
    checkers = min(5, num)
    if color == 'white': text_color = 'black'
    else: text_color = 'white'
    if pos >= 18:
        for i in range(checkers):
            x = canvas.create_oval(marg[0]+320+40*(pos-18), marg[1]+40+40*i, marg[0]+360+40*(pos-18),  marg[1]+80+40*i, fill=color)
            if num > 5:
                canvas.create_text(marg[0]+340+40*(pos-18), marg[1]+220, text=str(num), fill=text_color)
            if color == 'white': canvas.tag_bind(x, "<Button-1>", lambda k: move_fn(canvas, boardinfo, pos))

    elif pos >= 12:
        for i in range(checkers):
            x = canvas.create_oval(marg[0]+40+40*(pos-12), marg[1]+40+40*i, marg[0]+80+40*(pos-12), marg[1]+80+40*i, fill=color)
            if num > 5:
                canvas.create_text(marg[0]+60+40*(pos-12), marg[1]+220, text=str(num), fill=text_color)
            if color == 'white': canvas.tag_bind(x, "<Button-1>", lambda k: move_fn(canvas, boardinfo, pos))
    elif pos >= 6:
        for i in range(checkers):
            x = canvas.create_oval(marg[0]+240-40*(pos-6), marg[1]+480-40*i, marg[0]+280-40*(pos-6), marg[1]+520-40*i, fill=color)
            if num > 5:
                canvas.create_text(marg[0]+260-40*(pos-6), marg[1]+340, text=str(num), fill=text_color)
            if color == 'white': canvas.tag_bind(x, "<Button-1>", lambda k: move_fn(canvas, boardinfo, pos))
    else:
        for i in range(checkers):
            x = canvas.create_oval(marg[0]+520-40*(pos), marg[1]+480-40*i, marg[0]+560-40*(pos), marg[1]+520-40*i, fill=color)
            if num > 5:
                canvas.create_text(marg[0]+540-40*(pos), marg[1]+340, text=str(num), fill=text_color)
            if color == 'white': canvas.tag_bind(x, "<Button-1>", lambda k: move_fn(canvas, boardinfo, pos))

def create_dice(canvas, boardinfo):
    x = canvas.create_image(marg[0]+420, marg[1]+280, image=boardinfo.dice1)
    canvas.tag_bind(x, "<Button-1>", lambda k: swap_fn(canvas, boardinfo))

    y = canvas.create_image(marg[0]+460, marg[1]+280, image=boardinfo.dice2)
    canvas.tag_bind(y, "<Button-1>", lambda k: swap_fn(canvas, boardinfo))

def unpack_analysis(lines):
    text = ""
    for line in lines:
        text += (line + '\n')
    return text

def handle_regular(move, log_dict, dice, is_capture):
    print("handle regular", move.pos, log_dict, dice, is_capture)
    if not move: return False
    old_pos, new_pos = move.pos[0], move.pos[1]
    if (old_pos, new_pos, is_capture) in log_dict:
        log_dict[(old_pos, new_pos, is_capture)] -= 1
        if log_dict[(old_pos, new_pos, is_capture)] == 0:
            del log_dict[(old_pos, new_pos, is_capture)]
        return True

    elif (old_pos, old_pos - dice[0], False) in log_dict:
        move.pos[0] = old_pos - dice[0]
        log_dict[(old_pos, move.pos[0], False)] -= 1
        if log_dict[(old_pos, move.pos[0], False)] == 0:
            del log_dict[(old_pos, move.pos[0], False)]
        return handle_regular(move, log_dict, dice, is_capture)
    
    elif (old_pos, old_pos - dice[1], False) in log_dict:
        move.pos[0] = old_pos - dice[1]
        log_dict[(old_pos, move.pos[0], False)] -= 1
        if log_dict[(old_pos, move.pos[0], False)] == 0:
            del log_dict[(old_pos, move.pos[0], False)]
        return handle_regular(move, log_dict, dice, is_capture)
    
    else:
        return False

def isDecisionMatch(line, boardinfo):
    print("Decision match", re.split(r'[+-]+', line)[0], boardinfo.isDouble, boardinfo.isTake, boardinfo.isPass, boardinfo.isRoll)
    if boardinfo.isCube:
        decision = re.split(r'[+-]+', line)[0]
        if decision.startswith("Double, take"):
            print(boardinfo.isDouble and boardinfo.isTake)
            return boardinfo.isDouble and boardinfo.isTake
        elif decision.startswith("Double, pass"):
            print(boardinfo.isDouble and boardinfo.isPass)
            return boardinfo.isDouble and boardinfo.isPass
        else:
            print(boardinfo.isRoll)
            return boardinfo.isRoll
    else:
        move_list = getMoves(line)
        log_dict = Counter(boardinfo.movelog) # (old_pos, new_pos, is_capture)
        for move in move_list:
            print("MOVE", move)
            class_move = Move(move)
            print("CAT", class_move.cat, class_move.pos, class_move.mult)
            print("BOARD", boardinfo.movelog)
            if class_move.cat == "regular":
                if not handle_regular(class_move, log_dict, boardinfo.dice, False): return False
            elif class_move.cat == "capture":
                if not handle_regular(class_move, log_dict, boardinfo.dice, True): return False
            elif class_move.cat == "double":
                for i in range(class_move.mult):
                    print(i, "i")
                    if not handle_regular(copy.deepcopy(class_move), log_dict, boardinfo.dice, False): return False
            elif class_move.cat == "pick_pass":
                first_move = copy.copy(class_move)
                first_move.pos = [class_move.pos[0], class_move.pos[1]]
                second_move = copy.copy(class_move)
                second_move.pos = [class_move.pos[1], class_move.pos[2]]
                
                if not handle_regular(first_move, log_dict, boardinfo.dice, True): return False
                if not handle_regular(second_move, log_dict, boardinfo.dice, False): return False
        print("Done compare", log_dict)
        return len(log_dict) == 0

def configure_board(canvas, boardinfo, mode="none", analysis=None):
    global app, root_dir
    # board design
    canvas.create_rectangle(marg[0]+40, marg[1]+40, marg[0]+560, marg[1]+520, fill='gray')
    canvas.create_rectangle(marg[0], marg[1], marg[0]+600, marg[1]+40, fill='black')
    canvas.create_rectangle(marg[0], marg[1]+650, marg[0]+600, marg[1]+560, fill='black')
    canvas.create_rectangle(marg[0], marg[1]+40, marg[0]+40, marg[1]+520, fill='brown')
    canvas.create_rectangle(marg[0]+560, marg[1]+40, marg[0]+600, marg[1]+520, fill='brown')
    canvas.create_rectangle(marg[0]+280, marg[1]+40, marg[0]+320, marg[1]+520, fill='brown')

    canvas.create_line(marg[0]+300, marg[1]+40, marg[0]+300, marg[1]+520, width=2)

    for i in range(3):
        # top left points
        canvas.create_polygon([marg[0]+40+80*i, marg[1]+40, marg[0]+80+80*i, marg[1]+40, marg[0]+60+80*i, marg[1]+240], fill='green')
        canvas.create_text(marg[0]+60+80*i, marg[1]+30, text=str(13+2*i), font=("Arial", 10), fill='white')
        canvas.create_polygon([marg[0]+80+80*i, marg[1]+40, marg[0]+120+80*i, marg[1]+40, marg[0]+100+80*i, marg[1]+240], fill='lime')
        canvas.create_text(marg[0]+100+80*i, marg[1]+30, text=str(14+2*i), font=("Arial", 10), fill='white')

        # top right points
        canvas.create_polygon([marg[0]+320+80*i, marg[1]+40, marg[0]+360+80*i, marg[1]+40, marg[0]+340+80*i, marg[1]+240], fill='green')
        canvas.create_text(marg[0]+340+80*i, marg[1]+30, text=str(19+2*i), font=("Arial", 10), fill='white')
        canvas.create_polygon([marg[0]+360+80*i, marg[1]+40, marg[0]+400+80*i, marg[1]+40, marg[0]+380+80*i, marg[1]+240], fill='lime')
        canvas.create_text(marg[0]+380+80*i, marg[1]+30, text=str(20+2*i), font=("Arial", 10), fill='white')

        # bottom left points
        canvas.create_polygon([marg[0]+40+80*i, marg[1]+520, marg[0]+80+80*i, marg[1]+520, marg[0]+60+80*i, marg[1]+320], fill='lime')
        canvas.create_text(marg[0]+60+80*i, marg[1]+530, text=str(12-2*i), font=("Arial", 10), fill='white')
        canvas.create_polygon([marg[0]+80+80*i, marg[1]+520, marg[0]+120+80*i, marg[1]+520, marg[0]+100+80*i, marg[1]+320], fill='green')
        canvas.create_text(marg[0]+100+80*i, marg[1]+530, text=str(11-2*i), font=("Arial", 10), fill='white')

        # bottom right points
        canvas.create_polygon([marg[0]+320+80*i, marg[1]+520, marg[0]+360+80*i, marg[1]+520, marg[0]+340+80*i, marg[1]+320], fill='lime')
        canvas.create_text(marg[0]+340+80*i, marg[1]+530, text=str(6-2*i), font=("Arial", 10), fill='white')
        canvas.create_polygon([marg[0]+360+80*i, marg[1]+520, marg[0]+400+80*i, marg[1]+520, marg[0]+380+80*i, marg[1]+320], fill='green')
        canvas.create_text(marg[0]+380+80*i, marg[1]+530, text=str(5-2*i) , font=("Arial", 10), fill='white')

    # pip counts
    canvas.delete(canvas.white_pip_count)
    canvas.white_pip_count = canvas.create_text(marg[0]+300, marg[1]+20, text=str(boardinfo.black_pip_count), font=myfont, fill='white')
    canvas.delete(canvas.black_pip_count)
    canvas.black_pip_count = canvas.create_text(marg[0]+300, marg[1]+540, text=str(boardinfo.white_pip_count), font=myfont, fill='white')

    # checkers on board
    for i in range(24):
        checkers = boardinfo.board[i]
        if checkers > 0:
            place_checkers(canvas, boardinfo, i, checkers, 'white')
        elif checkers < 0:
            place_checkers(canvas, boardinfo, i, -checkers, 'black')

    # bar checkers
    if boardinfo.white_bar > 0:
        bar = canvas.create_oval(marg[0]+280, marg[1]+160, marg[0]+320, marg[1]+200, fill='white')
        if boardinfo.white_bar > 1:
            bar_txt = canvas.create_text(marg[0]+300, marg[1]+180, text=str(boardinfo.white_bar), font=myfont, fill='black')
            canvas.tag_bind(bar_txt, "<Button-1>", lambda k: move_fn(canvas, boardinfo, 24))
        canvas.tag_bind(bar, "<Button-1>", lambda k: move_fn(canvas, boardinfo, 24))

    if boardinfo.black_bar > 0:
        x = canvas.create_oval(marg[0]+280, marg[1]+360, marg[0]+320, marg[1]+400, fill='black')
        if boardinfo.black_bar > 1:
            canvas.create_text(marg[0]+300, marg[1]+380, text=str(boardinfo.black_bar), font=myfont, fill='white')

    # home checkers
    for i in range(boardinfo.white_home):
        canvas.create_rectangle(marg[0]+565, marg[1]+462-8*i, marg[0]+595, marg[1]+470-8*i, fill='white', outline='black')
    if boardinfo.white_home > 0:
        canvas.create_text(marg[0]+580, marg[1]+480, text=str(boardinfo.white_home), fill='white')

    for i in range(boardinfo.black_home):
        canvas.create_rectangle(marg[0]+565, marg[1]+90+8*i, marg[0]+595, marg[1]+98+8*i, fill='black', outline='white')
    if boardinfo.black_home > 0:
        canvas.create_text(marg[0]+580, marg[1]+80, text=str(boardinfo.black_home), fill='white')
    
    # cube info
    if boardinfo.cube_pos == 0:
        canvas.create_rectangle(marg[0]+285, marg[1]+265, marg[0]+315, marg[1]+295, fill='white', outline='black')
        canvas.create_text(marg[0]+300, marg[1]+280, text='64', font=myfont, fill='black')
    elif boardinfo.cube_pos == 1:
        canvas.create_rectangle(marg[0]+5, marg[1]+480, marg[0]+35, marg[1]+510, fill='white', outline='black')
        canvas.create_text(marg[0]+20, marg[1]+495, text=boardinfo.cube, font=myfont, fill='black')
    else:
        canvas.create_rectangle(marg[0]+5, marg[1]+50, marg[0]+35, marg[1]+80, fill='white', outline='black')
        canvas.create_text(marg[0]+20, marg[1]+65, text=boardinfo.cube, font=myfont, fill='black')

    # score info
    canvas.create_text(marg[0]+580, marg[1]+60, text=boardinfo.score_top + "/" + boardinfo.length, font=("Arial", 14), fill='white')
    canvas.create_text(marg[0]+580, marg[1]+500, text=boardinfo.score_bot + "/" + boardinfo.length, font=("Arial", 14), fill='white')

    # outside the board

    # title
    title = sys.argv[1].replace('_', ' ')
    if title == "temp":
        title = sys.argv[3]
    index = title.find('/')
    canvas.create_text(canvas_dims[0] // 2, marg[1] // 3, text = title[index+1:], font=myfont, fill='white')

    # position no.
    canvas.delete(canvas.position_counter)
    canvas.position_counter = canvas.create_text(canvas_dims[0] // 2, 4 * marg[1] // 5, \
            text="Positon #" + str(app.current_index) + " out of " + str(num_positions), \
            font=myfont, fill='white')

    # stats
    canvas.delete(canvas.stats)
    canvas.stats = canvas.create_text(canvas_dims[0] // 2, canvas_dims[1] - 20, \
            text="Correct: " + str(app.correct) + "\tMistake: " + str(app.mistakes) + "\tBlunders: " + str(app.blunders), \
            font=myfont, fill='white')

    # restart, exit, and copy XGID buttons
    restart_btn = canvas.create_rectangle(15, 10, 75, 40, fill='white')
    restart_txt = canvas.create_text(45, 25, text="Restart", fill='black')
    canvas.tag_bind(restart_btn, "<Button-1>", lambda k : restart_fn("all"))
    canvas.tag_bind(restart_txt, "<Button-1>", lambda k : restart_fn("all"))

    exit_btn = canvas.create_rectangle(615, 10, 675, 40, fill='white')
    exit_txt = canvas.create_text(645, 25, text="Exit", fill='black')
    canvas.tag_bind(exit_btn, "<Button-1>", lambda k : exit_fn())
    canvas.tag_bind(exit_txt, "<Button-1>", lambda k : exit_fn())

    copy_xgid_btn = canvas.create_rectangle(90, 10, 150, 40, fill='white')
    copy_xgid_txt = canvas.create_text(120, 25, text="Copy", fill='black')
    canvas.tag_bind(copy_xgid_btn, "<Button-1>", lambda k : copy_xgid_fn(boardinfo.xgid))
    canvas.tag_bind(copy_xgid_txt, "<Button-1>", lambda k : copy_xgid_fn(boardinfo.xgid))

    print("analysis mode", analysis)
    # analysis mode
    if analysis:
        message = 'Blunder!'
        found_best_move = False
        canvas.create_rectangle(marg[0], marg[1]+10, marg[0]+board_dims[0], marg[1]+board_dims[1]-10, fill='white', stipple="gray75")
        for i in range(len(analysis[0])):
            if (not found_best_move) and (isDecisionMatch(analysis[0][i], boardinfo)):
                canvas.create_rectangle(marg[0]+15, marg[1]+32 + 35*i, marg[0]+575, marg[1]+68 + 35*i, fill='mediumpurple1')
                if analysis[1][i] == 'green':
                    message = "Correct!"
                    app.incr_stats("correct")
                elif analysis[1][i] == 'blue':
                    message = "Mistake!"
                    app.incr_stats("mistake")
                    shutil.copy(boardinfo.file_path, root_dir + "mistakes")
                else:
                    message = "Blunder!"
                    app.incr_stats("blunder")
                    shutil.copy(boardinfo.file_path, root_dir + "mistakes")
                    shutil.copy(boardinfo.file_path, root_dir + "blunders")
                found_best_move = True
            canvas.create_text(marg[0]+300, marg[1]+50 + 35 * i, text=analysis[0][i], font=("Courier", 20, "bold"), fill=analysis[1][i])
        canvas.create_text(marg[0]+300, marg[1]+100 + 35 * len(analysis[0]), text=message, font=("Arial", 36, "bold"), fill='black')
        if not found_best_move:
            app.incr_stats("blunder")
            shutil.copy(boardinfo.file_path, root_dir + "mistakes")
            shutil.copy(boardinfo.file_path, root_dir + "blunders")

        next_btn = canvas.create_rectangle(marg[0]+530, marg[1]+500, marg[0]+590, marg[1]+530, fill='white')
        next_txt = canvas.create_text(marg[0]+560, marg[1]+515, text="Next ->", font=mysmallfont)
        canvas.tag_bind(next_btn, "<Button-1>", lambda k : next_fn())
        canvas.tag_bind(next_txt, "<Button-1>", lambda k : next_fn())
    # game mode
    else:
        if boardinfo.isCube:
            if boardinfo.isDouble:
                take_btn = canvas.create_rectangle(marg[0]+375, marg[1]+265, marg[0]+435, marg[1]+295, fill='white')
                take_txt = canvas.create_text(marg[0]+405, marg[1]+280, text="Take", font=mysmallfont)
                canvas.tag_bind(take_btn, "<Button-1>", lambda k : take_fn(canvas, boardinfo, analysis))
                canvas.tag_bind(take_txt, "<Button-1>", lambda k : take_fn(canvas, boardinfo, analysis))
                
                pass_btn = canvas.create_rectangle(marg[0]+445, marg[1]+265, marg[0]+505, marg[1]+295, fill='white')
                pass_txt = canvas.create_text(marg[0]+475, marg[1]+280, text="Pass", font=mysmallfont)
                canvas.tag_bind(pass_btn, "<Button-1>", lambda k : pass_fn(canvas, boardinfo, analysis))
                canvas.tag_bind(pass_txt, "<Button-1>", lambda k : pass_fn(canvas, boardinfo, analysis))
            else:
                roll_btn = canvas.create_rectangle(marg[0]+375, marg[1]+265, marg[0]+435, marg[1]+295, fill='white')
                roll_txt = canvas.create_text(marg[0]+405, marg[1]+280, text="Roll", font=mysmallfont)
                canvas.tag_bind(roll_btn, "<Button-1>", lambda k : rollDice_fn(canvas, boardinfo, analysis))
                canvas.tag_bind(roll_txt, "<Button-1>", lambda k : rollDice_fn(canvas, boardinfo, analysis))

                double_btn = canvas.create_rectangle(marg[0]+445, marg[1]+265, marg[0]+505, marg[1]+295, fill='white')
                double_txt = canvas.create_text(marg[0]+475, marg[1]+280, text="Double", font=mysmallfont)
                canvas.tag_bind(double_btn, "<Button-1>", lambda k : double_fn(canvas, boardinfo, analysis))
                canvas.tag_bind(double_txt, "<Button-1>", lambda k : double_fn(canvas, boardinfo, analysis))
        else:
            if (len(boardinfo.movelog) == 0):
                print(boardinfo.dice)
                canvas.num_moves, canvas.moves_length = getNumMoves(boardinfo.xgid, boardinfo.dice, boardinfo.white_home)
                print("canvas", canvas.num_moves, canvas.moves_length)
                if canvas.num_moves == 1 and canvas.moves_length != None:
                    print("num moves = 1")
                    new_dice = (canvas.moves_length, boardinfo.dice[1])
                    boardinfo.dice = new_dice
                create_dice(canvas, boardinfo)

            else:
                if (len(boardinfo.movelog) > 0):
                    undo_btn = canvas.create_rectangle(marg[0]+95, marg[1]+265, marg[0]+155, marg[1]+295, fill='white')
                    undo_txt = canvas.create_text(marg[0]+125, marg[1]+280, text='Undo', font=mysmallfont)
                    canvas.tag_bind(undo_btn, "<Button-1>", lambda k : undo_fn(canvas, boardinfo))
                    canvas.tag_bind(undo_txt, "<Button-1>", lambda k : undo_fn(canvas, boardinfo))

                if (len(boardinfo.movelog) == canvas.num_moves):
                    done_btn = canvas.create_rectangle(marg[0]+165, marg[1]+265, marg[0]+225, marg[1]+295, fill='white')
                    done_txt = canvas.create_text(marg[0]+195, marg[1]+280, text='Done', font=mysmallfont)
                    canvas.tag_bind(done_btn, "<Button-1>", lambda k : done_fn(canvas, boardinfo))
                    canvas.tag_bind(done_txt, "<Button-1>", lambda k : done_fn(canvas, boardinfo))

    return (app.correct, app.mistakes, app.blunders)


def rollDice_fn(canvas, boardinfo, analysis):
    print("roll dice")
    boardinfo.isRoll = True
    app.analysis = True
    app.show_canvas(boardinfo=boardinfo)

def take_fn(canvas, boardinfo, analysis):
    print("take pressed")
    boardinfo.isTake = True
    app.analysis = True
    app.show_canvas(boardinfo=boardinfo)

def pass_fn(canvas, boardinfo, analysis):
    print("pass pressed")
    boardinfo.isPass = True
    app.analysis = True
    app.show_canvas(boardinfo=boardinfo)

def double_fn(canvas, boardinfo, analysis):
    print("double pressed")
    boardinfo.isDouble = True
    configure_board(canvas, boardinfo, analysis)
    return

def move_white_help(boardinfo, old_pos, new_pos):
    if old_pos == 24:
        boardinfo.white_bar -= 1
        boardinfo.white_pip_count -= 25
    elif old_pos < 0:
        boardinfo.white_home -= 1
    else:
        boardinfo.board[old_pos] -= 1
        boardinfo.white_pip_count -= old_pos + 1

    if new_pos < 0:
        boardinfo.white_home += 1
    elif new_pos == 24:
        boardinfo.white_bar += 1
        boardinfo.white_pip_count += 25
    else:
        boardinfo.board[new_pos] += 1
        boardinfo.white_pip_count += new_pos + 1


def capture_black(boardinfo, pos):
    boardinfo.board[pos] += 1
    boardinfo.black_bar += 1
    boardinfo.black_pip_count += (pos + 1)

def uncapture_black(boardinfo, pos):
    boardinfo.board[pos] -= 1
    boardinfo.black_bar -= 1
    boardinfo.black_pip_count -= (pos + 1)

def find_max_checker(board, white_bar):
    if white_bar > 0:
        return 25

    for i in range(len(board)-1, -1, -1):
        if board[i] > 0:
            return i + 1
    return 0

def move_fn(canvas, boardinfo, pos):
    print("move!!!")
    # find furthest checker back
    max_checker = find_max_checker(boardinfo.board, boardinfo.white_bar)
    if boardinfo.dice[0] == boardinfo.dice[1]:
        # only move one checker
        new_pos = pos - boardinfo.dice[0]
    else:
        # can move with one or two dice
        new_pos = pos - boardinfo.dice[len(boardinfo.movelog)]
    print(new_pos, boardinfo.dice, max_checker)
    is_capture = False
    if new_pos >= 0 and boardinfo.board[new_pos] < -1: return # new pos is blocked
    if new_pos >= 0 and boardinfo.board[new_pos] == -1: # capture black piece
        capture_black(boardinfo, new_pos)
        is_capture = True
    if new_pos < 0 and max_checker > 6: return # new pos is outside the board and bear off stage not yet reached
    if new_pos < -1 and max_checker != pos+1: return # cannot bear off with wastage if a higher checker exists

    move_white_help(boardinfo, pos, new_pos) # move white piece

    boardinfo.movelog.append((pos+1, max(new_pos+1, 0), is_capture))

    print("LOG", boardinfo.movelog)
    configure_board(canvas, boardinfo)
    return

def undo_fn(canvas, boardinfo):
    old_pos, new_pos, is_capture = boardinfo.movelog.pop()
    move_white_help(boardinfo, new_pos-1, old_pos-1)
    if is_capture:
        uncapture_black(boardinfo, new_pos-1)

    configure_board(canvas, boardinfo)
    print("LOG", boardinfo.movelog)
    return

def done_fn(canvas, boardinfo):
    app.analysis = True
    app.show_canvas(boardinfo=boardinfo)
    return

def swap_fn(canvas, boardinfo):
    if len(boardinfo.movelog) > 0: return # can't swap dice mid move
    new_dice = (boardinfo.dice[1], boardinfo.dice[0])
    boardinfo.dice = new_dice
    tmp = boardinfo.dice1
    boardinfo.dice1 = boardinfo.dice2
    boardinfo.dice2 = tmp
    configure_board(canvas, boardinfo)

def next_fn():
    app.analysis = False
    app.switch_right(None)

def exit_fn():
    global root

    root.destroy()

def restart_fn(mode):
    global root_dir

    root.destroy()
    print("SYS", sys.argv)
    if mode == "play again":
        os.execlp("python", "python", "flashcard.py", sys.argv[3])
        return
    elif mode == "all":
        os.execlp("python", "python", "flashcard.py", sys.argv[1], sys.argv[2], sys.argv[3])
        return
    elif mode == "mistakes":
        if os.path.exists(root_dir + "temp"):
            shutil.rmtree(root_dir + "temp")
        os.rename(root_dir + "mistakes", root_dir + "temp")
    else:
        if os.path.exists(root_dir + "temp"):
            shutil.rmtree(root_dir + "temp")
        os.rename(root_dir + "blunders", root_dir + "temp")
    os.execlp("python", "python", "flashcard.py", "temp", mode, sys.argv[3])

def copy_xgid_fn(xgid):
    pyperclip.copy(xgid)

def analysis(q, cache_directory):
    while True:
        print("start thread")
        xgid_line = q.get()
        xgid_filename = xgid.xgid_to_filename(xgid_line)
        if os.path.exists(cache_directory + xgid_filename):
            analysis_done.add(xgid_line)
        else:
            lines = eval.get_stats(xgid_line)
            print("RECEIVED LINES", lines)
            with open(cache_directory + xgid.xgid_to_filename(xgid_line), 'wb') as f:
                pickle.dump(lines, f)
            analysis_done.add(xgid_line)
        q.task_done()

def program():
    global num_positions, worker, root_dir
    if len(sys.argv) > 1:
        positions = sys.argv[1]
        full_positions = root_dir + positions
        print("Start", root_dir, positions, full_positions, sys.argv)

        if os.path.exists(root_dir + "blunders"):
            shutil.rmtree(root_dir + "blunders")
        os.mkdir(root_dir + "blunders")
        if os.path.exists(root_dir + "mistakes"):
            shutil.rmtree(root_dir + "mistakes")
        os.mkdir(root_dir + "mistakes")

        q = queue.Queue()
        worker = Thread(target = analysis, args =(q, root_dir + r"cache\\", ))
        worker.start()

        num_positions = len(os.listdir(full_positions))
        app.create_intro()
        position_list = os.listdir(full_positions)[:]
        random.shuffle(position_list)
        for filename in position_list:
            print("Filename", filename)
            file_path = os.path.join(full_positions, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    graph = pickle.load(f)
                xgid = graph.xgid
                q.put(xgid)
                app.create_canvas(xgid, file_path)
        app.current_index = 0
        app.show_canvas()
        root.mainloop()
        q.join()

    else:
        print("ERROR: need an argument");

def main():
    # Example: python flashcard.py fout
    if len(sys.argv) == 2:
        sys.argv.append("all")
        sys.argv.append(sys.argv[1])
    program()

if __name__ == "__main__":
    main()
