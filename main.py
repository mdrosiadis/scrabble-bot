from dataclasses import dataclass
import enum
import pprint
import copy
from typing import NamedTuple
from colorama import Back, Fore, Style
import time

from searcher import PlayWord, PlayLetter, QueryResult, fulfills_query, create_greek_trie, playword_to_str

BOARD_SIZE = 15

class LetterData(NamedTuple):
    letter: str
    n_count: int
    value: int


class Orientation(enum.Enum):
    HORIZONTAL = enum.auto()
    VERTICAL   = enum.auto()


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

letter_values = {ld.letter: ld.value for ld in LETTER_DATA}


@dataclass
class PositionedWord:
    word: PlayWord
    start_pos: tuple[int, int]
    orientation: Orientation


def get_cell_style(cell: Cell):
    style = Fore.WHITE  + Style.DIM

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


game_board = [ [PlayLetter(letter=" ")] * BOARD_SIZE for _ in range(BOARD_SIZE)]


def play_word(game_board, word: PlayWord, pos: tuple[int, int], orientation: Orientation, place_letters=True) -> int|None:
    points = 0

    step_x = 1 if orientation == orientation.HORIZONTAL else 0
    step_y = 1 if orientation == orientation.VERTICAL else 0


    # dry run 
    cur_x, cur_y = pos
    for play_letter in word:
        board_letter = game_board[cur_y][cur_x]

        if not fulfills_query(play_letter.real_letter, board_letter.real_letter):
            return None

        # TODO: check in the oposite direction

        cur_x += step_x
        cur_y += step_y

    # now place the letters
    multuplier = 1
    points = 0

    cur_x, cur_y = pos
    for play_letter in word:
        board_letter = game_board[cur_y][cur_x]


        if board_letter.real_letter == " ":
            letter_points = letter_values[play_letter.letter]

            if place_letters:
                game_board[cur_y][cur_x] = play_letter

            cell = BOARD[cur_y][cur_x]

            match cell:
                case Cell.DOUBLE_LETTER:
                    letter_points *= 2

                case Cell.TRIPLE_LETTER:
                    letter_points *= 3

                case Cell.DOUBLE_WORD:
                    multuplier *= 2

                case Cell.TRIPLE_WORD:
                    multuplier *= 3 

        else:
            letter_points = letter_values[board_letter.letter]

        points += letter_points

        cur_x += step_x
        cur_y += step_y

    points *= multuplier

    return points


def play_positioned_word(game_board, pw: PositionedWord, place_letters=True):
    return play_word(game_board, pw.word, pw.start_pos, pw.orientation, place_letters=place_letters)


def playword_from_str(s: str, wildcards: list[str]|str = "") -> PlayWord|None:
    n_wilds = s.count("*")

    # we should have all wildcard replacements
    if isinstance(wildcards, str):
        wildcards = list(wildcards)

    if len(wildcards) != n_wilds:
        return None

    wildcard_index = 0
    play_word = []

    for letter in s:
        real_letter = letter
        if letter == "*":
            real_letter = wildcards[wildcard_index]
            wildcard_index += 1

        pl = PlayLetter(letter=letter, wildcard_letter=real_letter)
        play_word.append(pl)


    return play_word





def render_board(game_board):
    for y, row in enumerate(BOARD):
        for x, cell in enumerate(row):
            style = get_cell_style(cell)
            wildcard_mark = " "
            if game_board[y][x].letter == "*":
                wildcard_mark = "*"

            content = f" {game_board[y][x].real_letter}{wildcard_mark}"
            print(style + f" {content} " + Style.RESET_ALL, end="")

        print()




T = create_greek_trie()


def find_words(game_board, letters: str) -> list[PositionedWord]:
    results = []
    # find horizontal
    for y, row in enumerate(game_board):
        query = "".join(pl.real_letter for pl in row)
        ret = T.query(query, letters)
        
        ret = [PositionedWord(word=w.word, start_pos=(w.start_index, y), orientation=Orientation.HORIZONTAL) for w in ret]
        results.extend(ret)


    # find vertical
    for x in range(BOARD_SIZE):
        col = [game_board[y][x] for y in range(BOARD_SIZE)]
        query = "".join(pl.real_letter for pl in col)
        ret = T.query(query, letters)
        
        ret = [PositionedWord(word=w.word, start_pos=(x, w.start_index), orientation=Orientation.VERTICAL) for w in ret]
        results.extend(ret)

    return results



render_board(game_board)


to_play = playword_from_str("ΑΠΟ*Η", "Ψ")
if to_play is not None:
    ret = play_word(game_board, to_play, (4, BOARD_SIZE//2 ), Orientation.HORIZONTAL)


to_play = playword_from_str("ΤΑΨΙ")
if to_play is not None:
    ret = play_word(game_board, to_play, (7, 5), Orientation.VERTICAL)

to_play = playword_from_str("ΤΗΓΑΝΙΑ")
if to_play is not None:
    ret = play_word(game_board, to_play, (7, 5), Orientation.HORIZONTAL)

for _ in range(3):
    print()


render_board(game_board)


t0 = time.time()
found = find_words(game_board, "ΟΥ")
diff = time.time() - t0

print(f"Found {len(found)} words in {diff:.2f} seconds.")


def temp_play(idx):
    pw = found[idx]
    pws = playword_to_str(pw.word)

    temp_board = copy.deepcopy(game_board)
    points = play_positioned_word(temp_board, pw)

    print("Playing word:", pws, pw.start_pos, pw.orientation, "Points:", points)

    render_board(temp_board)


