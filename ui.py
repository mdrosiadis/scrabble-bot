import tkinter as tk
import tkinter.ttk as ttk
from functools import partial
from main import BOARD, BOARD_SIZE, Cell, Orientation, create_empty_board, Board, get_words_sorted, play_positioned_word, play_word, playword_from_str, VALID_LETTERS
from threading import Thread
from tkinter.simpledialog import askstring
from tkinter.messagebox import askokcancel
import copy

from searcher import PlayLetter



CELL_COLORS = {
    Cell.SIMPLE: "green",
    Cell.DOUBLE_LETTER: "lightblue",
    Cell.TRIPLE_LETTER: "blue",
    Cell.DOUBLE_WORD: "orange",
    Cell.TRIPLE_WORD: "red",
}

CELL_FONT = ("TkDefaultFont", 24)

def font_size(sz):
    return ("TkDefaultFont", sz)


class GameFrame(tk.Frame):


    def __init__(self, master):
        super().__init__(master)

        self.game_board = create_empty_board()

        self.grid_rowconfigure(list(range(15)), weight=1)
        self.grid_columnconfigure(list(range(15)), weight=1)

        self.buttons = []
        for y in range(BOARD_SIZE):
            self.buttons.append([])
            for x in range(BOARD_SIZE):
                cell = BOARD[y][x]
                clr = CELL_COLORS[cell]
                btn = tk.Button(self, bg=clr, fg="white", font=CELL_FONT, text="", width=1)
                btn.config(command=partial(self.on_button_click, x, y))
                btn.grid(row=y, column=x, sticky=tk.NSEW)
                self.buttons[-1].append(btn)


    def on_button_click(self, x, y):
        letter = askstring("Enter letter", "Enter letter", initialvalue="")

        if letter is None:
            return

        letter = letter.upper()

        if letter == "":
            letter = " "

        if letter != " " and letter not in VALID_LETTERS:
            return

        self.buttons[y][x].config(text=letter)
        self.game_board[y][x] = PlayLetter(letter=letter)


    def set_board(self, board: Board):
        self.game_board = board

        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                self.buttons[y][x].config(text=self.game_board[y][x].real_letter)




class ScrabbleApp(tk.Frame):


    def __init__(self, master):
        super().__init__(master)


        self.results = []

        self.game_frame = GameFrame(self)
        self.controls_frame = tk.Frame(self)

        self.game_frame.pack(side=tk.LEFT)#  fill=tk.BOTH, expand=True)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.reset_button = tk.Button(self, bg='red', fg='white', text="RESET")
        self.reset_button.config(command=self.on_reset_click)
        self.reset_button.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self, text="Rack", font=font_size(18)).pack(fill=tk.X, padx=5, pady=5, anchor=tk.NW)

        self.rack_entry = tk.Entry(self, font=CELL_FONT)
        self.rack_entry.pack(fill=tk.X, padx=5, pady=5,)

        self.find_button = tk.Button(self, text="Find", font=font_size(20))
        self.find_button.config(command=self.on_find_clicked)
        self.find_button.pack(fill=tk.X, padx=5, pady=5,)


        self.results_listbox = tk.Listbox(self, font=font_size(16))
        self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        self.results_listbox.bind("<<ListboxSelect>>", self.on_listbox_clicked)

        self.clear_button = tk.Button(self, text="Clear edit", font=font_size(20))
        self.clear_button.config(command=self.on_clear_click)
        self.clear_button.pack(fill=tk.X, padx=5, pady=5,)

        self.initialize()


    def initialize(self):
        self.results = []
        self.results_listbox.delete(0, tk.END)

        self.game_board = create_empty_board()
        self.game_frame.set_board(self.game_board)



    def on_reset_click(self):
        if not askokcancel("Clear Board?", "Clear board?"):
            return

        self.initialize()



    def on_clear_click(self):
        self.game_frame.set_board(self.game_board)


    def on_find_clicked(self):
        self.game_board = self.game_frame.game_board
        letters = self.rack_entry.get().upper()

        self.results_listbox.delete(0, tk.END)
        self.results = get_words_sorted(self.game_board, letters)

        for result in self.results:
            self.results_listbox.insert(tk.END, result[-1])

    def on_listbox_clicked(self, evt):
        selection = self.results_listbox.curselection()[0]

        if len(self.results) == 0:
            return

        temp_board = copy.deepcopy(self.game_board)
        positioned_word = self.results[selection][0]

        points = play_positioned_word(self.game_board, positioned_word, nxt=temp_board)

        self.game_frame.set_board(temp_board)





if __name__ == "__main__":
    app = tk.Tk()
    app.geometry("1200x600")
    app.title("ScrabbleApp")


    scrabble = ScrabbleApp(app)
    scrabble.pack(fill=tk.BOTH, expand=True)




    app.mainloop()



