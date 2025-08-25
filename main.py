import enum
from typing import NamedTuple
from colorama import Back, Fore, Style

BOARD_SIZE = 15

class LetterData(NamedTuple):
    letter: str
    n_count: int
    value: int


class Cell(enum.Enum):
    SIMPLE = enum.auto()
    DOUBLE_LETTER = enum.auto()
    TRIPLE_LETTER = enum.auto()
    DOUBLE_WORD = enum.auto()
    TRIPLE_WORD = enum.auto()


SS = Cell.SIMPLE
DL = Cell.DOUBLE_LETTER
TL = Cell.TRIPLE_LETTER
DW = Cell.DOUBLE_WORD
TW = Cell.TRIPLE_WORD


BOARD = [
    [TW, SS, SS, DL, SS, SS, SS, TW, SS, SS, SS, DL, SS, SS, TW],
    [SS, DW, SS, SS, SS, TL, SS, SS, SS, TL, SS, SS, SS, DW, SS],
    [SS, SS, DW, SS, SS, SS, DL, SS, DL, SS, SS, SS, DW, SS, SS],
    [DL, SS, SS, DW, SS, SS, SS, DL, SS, SS, SS, DW, SS, SS, DL],
    [SS, SS, SS, SS, DW, SS, SS, SS, SS, SS, DW, SS, SS, SS, SS],
    [SS, TL, SS, SS, SS, TL, SS, SS, SS, TL, SS, SS, SS, TL, SS],
    [SS, SS, DL, SS, SS, SS, DL, SS, DL, SS, SS, SS, DL, SS, SS],
    [TW, SS, SS, DL, SS, SS, SS, DW, SS, SS, SS, DL, SS, SS, TW],
    [SS, SS, DL, SS, SS, SS, DL, SS, DL, SS, SS, SS, DL, SS, SS],
    [SS, TL, SS, SS, SS, TL, SS, SS, SS, TL, SS, SS, SS, TL, SS],
    [SS, SS, SS, SS, DW, SS, SS, SS, SS, SS, DW, SS, SS, SS, SS],
    [DL, SS, SS, DW, SS, SS, SS, DL, SS, SS, SS, DW, SS, SS, DL],
    [SS, SS, DW, SS, SS, SS, DL, SS, DL, SS, SS, SS, DW, SS, SS],
    [SS, DW, SS, SS, SS, TL, SS, SS, SS, TL, SS, SS, SS, DW, SS],
    [TW, SS, SS, DL, SS, SS, SS, TW, SS, SS, SS, DL, SS, SS, TW],
]

# http://greekscrabble.gr/wp-content/uploads/2021/02/ta-mystika-tou-scrabble.pdf

LETTER_DATA = [
    LetterData('Α', n_count=12, value= 1),
    LetterData('B', n_count= 1, value= 8),
    LetterData('Γ', n_count= 2, value= 4),
    LetterData('Δ', n_count= 2, value= 4),
    LetterData('Ε', n_count= 8, value= 1),
    LetterData('Ζ', n_count= 1, value=10),
    LetterData('Η', n_count= 7, value= 1),
    LetterData('Θ', n_count= 1, value=10),
    LetterData('Ι', n_count= 8, value= 1),
    LetterData('Κ', n_count= 4, value= 2),
    LetterData('Λ', n_count= 3, value= 3),
    LetterData('Μ', n_count= 3, value= 3),
    LetterData('Ν', n_count= 6, value= 1),
    LetterData('Ξ', n_count= 1, value=10),
    LetterData('Ο', n_count= 9, value= 1),
    LetterData('Π', n_count= 4, value= 2),
    LetterData('Ρ', n_count= 5, value= 2),
    LetterData('Σ', n_count= 7, value= 1),
    LetterData('Τ', n_count= 8, value= 1),
    LetterData('Υ', n_count= 4, value= 2),
    LetterData('Φ', n_count= 1, value= 8),
    LetterData('Χ', n_count= 1, value= 8),
    LetterData('Ψ', n_count= 1, value=10),
    LetterData('Ω', n_count= 3, value= 3),
    LetterData('*', n_count= 2, value= 0),
]


def get_cell_style(cell: Cell):
    style = Fore.WHITE  + Style.DIM
    back = ""

    match cell:
        case Cell.SIMPLE:
            style = Style.BRIGHT + Fore.WHITE + Back.RESET
        case Cell.DOUBLE_LETTER:
            style = Style.BRIGHT + Fore.BLACK + Back.CYAN
        case Cell.TRIPLE_LETTER:
            style = Style.BRIGHT + Fore.BLACK + Back.BLUE
        case Cell.DOUBLE_WORD:
            style = Style.BRIGHT + Fore.BLACK + Back.YELLOW
        case Cell.TRIPLE_WORD:
            style = Style.BRIGHT + Fore.BLACK + Back.RED

    return style
            


def render_board():
    for y, row in enumerate(BOARD):
        for x, cell in enumerate(row):
            style = get_cell_style(cell)
            content = "1"
            print(style + f" {content} " + Style.RESET_ALL, end="")

        print()



render_board()
