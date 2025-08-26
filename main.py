from dataclasses import dataclass
import enum
from os import remove, set_inheritable
import random
import pprint
import copy
from typing import List, NamedTuple
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


def create_empty_board():
    return [[PlayLetter(letter=" ")] * BOARD_SIZE for _ in range(BOARD_SIZE)]


game_board = create_empty_board()

@dataclass
class PositionedLetter:
    play_letter: PlayLetter
    pos: tuple[int, int]


def make_pletter(letter, x, y):
    return PositionedLetter(play_letter=PlayLetter(letter=letter), pos=(x, y))


@dataclass
class PlaceLettersResult:
    points: int
    expandable: list[tuple[PositionedLetter, Orientation]]

def play_letters(game_board, letters: list[PositionedLetter], nxt=None) -> int|None:
    pos_to_letter = {pl.pos: pl for pl in letters}
    visited = {pl.pos: [] for pl in letters}
    
    for pl in letters:
        if game_board[pl.pos[1]][pl.pos[0]].letter != " ":
            print("Could not play")
            return None
        

    @dataclass
    class ExpandResult:
        word: str
        multiplier: int
        points: int
        player_placed: int

    def expand(pos: tuple[int, int], orientation: Orientation, backwards: bool) -> ExpandResult:
        # if this letter is expanded already this orient
        # if orientation in visited[pos]:
        #     return 

        result = ExpandResult("", multiplier=1, points=0, player_placed=0)


        step_x = 1 if orientation == orientation.HORIZONTAL else 0
        step_y = 1 if orientation == orientation.VERTICAL else 0

        cur_x, cur_y = pos

        if backwards:
            cur_x += step_x
            cur_y += step_y

            step_x *= -1
            step_y *= -1


        # dry run 
        while True:
            cur_x += step_x
            cur_y += step_y

            if cur_x < 0 or cur_y < 0 or cur_x >= BOARD_SIZE or cur_y >= BOARD_SIZE:
                break

            npos = (cur_x, cur_y)

            is_board = False

            if npos in visited:
                visited[npos].append(orientation)
                letter = pos_to_letter[npos].play_letter

                if nxt:
                    nxt[cur_y][cur_x] = letter

            else:
                is_board = True
                letter = game_board[cur_y][cur_x]

            if letter.letter == " ":
                break

            result.word += letter.real_letter

            if not is_board:
                result.player_placed += 1
                letter_points = letter_values[letter.letter]

                cell = BOARD[cur_y][cur_x]

                match cell:
                    case Cell.DOUBLE_LETTER:
                        letter_points *= 2

                    case Cell.TRIPLE_LETTER:
                        letter_points *= 3

                    case Cell.DOUBLE_WORD:
                        result.multiplier *= 2

                    case Cell.TRIPLE_WORD:
                        result.multiplier *= 3 

            else:
                letter_points = letter_values[letter.letter]

            result.points += letter_points

        if backwards:
            result.word = result.word[::-1]

        return result


    total_points = 0

    not_expanded = []
    valids = []
    for pl in letters:
        # expland horizontal and vertical
        for orient in (Orientation.HORIZONTAL, Orientation.VERTICAL):
            if orient in visited[pl.pos]:
                continue

            back  = expand(pl.pos, orient, True)
            front = expand(pl.pos, orient, False)

            points = back.points + front.points
            multi = back.multiplier * front.multiplier

            word = back.word + front.word
            player_placed = back.player_placed + front.player_placed

            if len(word) < 2:
                not_expanded.append((pl, orient))
                continue

            # print("WORD:", word)
            word_valid = len(word) >= 2 and word in T.wordset
            if word_valid:
                # print("VALID")
                valids.append((word, points))
            else:
                # print("INVALID")

                return None


            word_points = points * multi

            if player_placed >= 7:
                # print("BONUS 50")
                word_points += 50


            # print("Points:", word_points)

            total_points += word_points


    return total_points



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


def get_positioned_word_letters(game_board, pw: PositionedWord) -> list[PositionedLetter]:
    step_x = 1 if pw.orientation == Orientation.HORIZONTAL else 0
    step_y = 1 if pw.orientation == Orientation.VERTICAL else 0


    result = []

    cur_x, cur_y = pw.start_pos

    for play_letter in pw.word:
        board_letter = game_board[cur_y][cur_x]

        if board_letter.letter == " ":
            result.append(PositionedLetter(play_letter, pos=(cur_x, cur_y)))

        cur_x += step_x
        cur_y += step_y

    return result


def play_positioned_word(game_board, pw: PositionedWord, place_letters=True, nxt=None):
    positioned_letters = get_positioned_word_letters(game_board, pw)

    return play_letters(game_board, positioned_letters, nxt=nxt)

#
# def play_positioned_word(game_board, pw: PositionedWord, place_letters=True):
#     return play_word(game_board, pw.word, pw.start_pos, pw.orientation, place_letters=place_letters)
#

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
    print(" " * 2, end="")
    for x in range(BOARD_SIZE):
        print(f"{x:3d}", end="")

    print()

    for y, row in enumerate(BOARD):
        print(f"{y:3d}", end="")
        for x, cell in enumerate(row):
            style = get_cell_style(cell)
            wildcard_mark = " "
            if game_board[y][x].letter == "*":
                wildcard_mark = "*"

            content = f" {game_board[y][x].real_letter}{wildcard_mark}"
            print(style + f"{content}" + Style.RESET_ALL, end="")

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



# to_play = playword_from_str("ΤΑΨΙ")
# if to_play is not None:
#     ret = play_word(game_board, to_play, (7, 5), Orientation.VERTICAL)
#
# to_play = playword_from_str("ΤΗΓΑΝΙΑ")
# if to_play is not None:
#     ret = play_word(game_board, to_play, (7, 5), Orientation.HORIZONTAL)
#
for _ in range(3):
    print()


render_board(game_board)


def get_best_word(game_board, letters):
    t0 = time.time()
    found = find_words(game_board, letters)
    diff = time.time() - t0

    print(f"Found {len(found)} words in {diff:.2f} seconds.")


    t0 = time.time()
    found_scores = []
    for pw in found:
        score = play_positioned_word(game_board, pw)

        if score is not None:
            found_scores.append((pw, score))


    found_scores.sort(key=lambda x: x[1], reverse=True)

    diff = time.time() - t0
    print(f"Found {len(found_scores)} valid scores in {diff:.2f} seconds.")


    rank = 0
    TOP_N = 3
    for pw, score in found_scores[:TOP_N]:
        rank += 1
        word = playword_to_str(pw.word)
        print(f"{rank:4d}) {word:15s} (Points: {score:3d})  / Pos: {pw.start_pos} {pw.orientation}")

    return found_scores[0][0]



play = [
    make_pletter("Μ", 10, 4),
    make_pletter("Γ", 10, 6),
    make_pletter("Ι", 10, 7),
    make_pletter("Κ", 10, 8),
    make_pletter("Ο", 10, 9),
    make_pletter("Υ", 10,10),
    make_pletter("Σ", 10,11),
    make_pletter("Α", 11, 4),
]

# demo 
@dataclass
class Player:
    name: str
    letters: list[PlayLetter]
    points: int = 0

    def pick_letters(self, bag):
        while len(self.letters) < 7 and len(bag) > 0:
            l = random.choice(bag)
            bag.remove(l)
            self.letters.append(l)


def remove_letter_from_list(letter, letter_list):
    remove_index = None
    for i, ll in enumerate(letter_list):
        if letter == ll.letter:
            remove_index = i 
            break
   
    assert remove_index is not None, "Played a letter we didnt have?!"
    letter_list.pop(remove_index)


from itertools import cycle


def demo():
    players = [
        Player("Player 1", [], 0),
        Player("Player 2", [], 0),
    ]

    player_iter = cycle(players)

    letter_bag = []
    for ld in LETTER_DATA:
        for _ in range(ld.n_count):
            letter_bag.append(PlayLetter(letter=ld.letter))


    random.shuffle(letter_bag)
    
    game_board = create_empty_board()


    wordlist = list(T.wordset)
    while True:
        first_word = random.choice(wordlist)
        if len(first_word) >= 2 and len(first_word) <= 7:
            break

    to_play = playword_from_str(first_word)
    if to_play is not None:
        pos_x = random.randint(BOARD_SIZE//2-len(first_word)+1, BOARD_SIZE//2)
        positioned_word = PositionedWord(to_play, (pos_x, BOARD_SIZE//2), Orientation.HORIZONTAL)

        next_board = copy.deepcopy(game_board)
        points = play_positioned_word(game_board, positioned_word, nxt=next_board)

        # remove letters
        letters_played = get_positioned_word_letters(game_board, positioned_word)
        for letter in letters_played:
            remove_letter_from_list(letter.play_letter.letter, letter_bag)

        game_board = next_board

    render_board(game_board)

    while len(letter_bag) > 0:
        player = next(player_iter)
        player.pick_letters(letter_bag)

        my_letters = "".join(pl.letter for pl in player.letters)

        print(f"{player.name} playing. Letters: {my_letters}")

        best_word = get_best_word(game_board, my_letters)

        next_board = copy.deepcopy(game_board)
        points = play_positioned_word(game_board, best_word, nxt=next_board)

        # remove letters
        letters_played = get_positioned_word_letters(game_board, best_word)
        for letter in letters_played:
            remove_letter_from_list(letter.play_letter.letter, player.letters)

            
        render_board(next_board)

        pws = playword_to_str(best_word.word)
        print(player.name, "played word:", pws, best_word.start_pos, best_word.orientation, "Points:", points)

        player.points += points
        print("Total points:", player.points)

        game_board = next_board


    for player in players:
        print(f"{player.name}: {player.points:4d} points")

# temp_board = copy.deepcopy(game_board)
# play_letters(game_board, play, temp_board)
#
# render_board(temp_board)

def temp_play(idx):
    pw = found_scores[idx][0]
    pws = playword_to_str(pw.word)

    temp_board = copy.deepcopy(game_board)
    points = play_positioned_word(temp_board, pw, nxt=temp_board)

    print("Playing word:", pws, pw.start_pos, pw.orientation, "Points:", points)

    render_board(temp_board)


