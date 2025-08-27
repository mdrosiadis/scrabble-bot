import pprint
from dataclasses import dataclass
import pickle
import time

@dataclass
class TrieEdge:
    letter: str
    index: int

@dataclass
class TrieNode:
    letter: str
    index: int
    depth: int
    terminal: bool
    parent: int
    edges: dict[str, int]


@dataclass
class PlayLetter:
    letter: str
    wildcard_letter: str = ""

    @property
    def real_letter(self):
        if self.letter == '*':
            return self.wildcard_letter

        return self.letter


PlayWord = list[PlayLetter]

def playword_to_str(play_word: PlayWord) -> str:
    return "".join(pl.real_letter for pl in play_word)

@dataclass
class QueryUpResult:
    prefix: PlayWord
    jumps: list[str]


@dataclass
class QueryResult:
    start_index: int
    word: PlayWord

    def __hash__(self):
        rw = ''.join(l.real_letter for l in self.word)
        return hash(f"{self.start_index}{rw}")


def get_jump_letter(letter_to_get: str, jumps: list[str]) -> str|None:
    """Return the letter used to jump to `letter_to_get`, else None"""
    if letter_to_get in jumps:
        return letter_to_get

    elif "*" in jumps:
        return "*"

    else:
        return None


def fulfills_query(letter: str, query_letter: str):
    return query_letter.isspace() or letter == query_letter # or letter == '*'

def debug_print_q_starts(q, s):
    qu_p = q.replace(' ', '.')
    points = [' '] * len(qu_p)
    for entry in s:
        points[entry] = '^'

    points_s = ''.join(points)

    print(qu_p)
    print(points_s)


class Trie:

    def __init__(self):
        self.wordset = set()
        self.nodes: list[TrieNode] = []
        self.node_tracker: dict[str, list[int]] = dict()

        # create root node
        self.nodes.append(TrieNode("", index=0, depth=0, terminal=False, parent=-1, edges=dict()))


    def create_node(self, letter:str, parent_idx: int):
        parent_node = self.nodes[parent_idx]
        new_node = TrieNode(
            letter=letter,
            index=len(self.nodes),
            depth=parent_node.depth+1,
            terminal=False,
            parent=parent_idx,
            edges=dict()
        )

        parent_node.edges[letter] = new_node.index
        self.nodes.append(new_node)

        if letter not in self.node_tracker:
            self.node_tracker[letter] = []

        self.node_tracker[letter].append(new_node.index)

        return self.nodes[-1]


    def add(self, word):
        self.wordset.add(word)
        current = self.nodes[0] # root

        for letter in word:
            if letter not in current.edges:
                self.create_node(letter, current.index)

            current = self.nodes[current.edges[letter]]


        # mark the final node as terminal
        current.terminal = True



    def _find_starts(self, query: str) -> list[int]:
        starts = []
        cur_entry = -1
        for i, l in enumerate(query):
            if not l.isspace():
                cur_entry = i
            else:
                if cur_entry != -1:
                    starts.append(cur_entry)
                cur_entry = -1

        if cur_entry != -1:
            starts.append(cur_entry)

        return starts
    
    def _query_up(self, node: TrieNode, query: str, query_start: int, jumps: list[str]) -> QueryUpResult|None:

        # prune big branches we wont fit
        if node.depth > query_start + 1:
            return None

        our_jumps = jumps.copy()

        # first walk up
        failed_up = False
        query_index = query_start
        prefix_builder: PlayWord = [PlayLetter(letter=node.letter)]
            # node.letter]

        while node.parent != 0:
            query_index -= 1
            parent_node = self.nodes[node.parent]

            # if out of bounds of query, stop searching
            if query_index < 0:
                return None


            query_letter = query[query_index]
            # if query has another fixed letter up and we
            # do not match, stop searching
            if not fulfills_query(parent_node.letter, query_letter):
                return None

            # if next query up is space, we should just have
            # an available jump
            jmp = parent_node.letter
            if query_letter.isspace():
                jmp = get_jump_letter(parent_node.letter, our_jumps)
                if jmp is None:
                    return None

                our_jumps.remove(jmp)


            prefix_builder.append(PlayLetter(letter=jmp, wildcard_letter=parent_node.letter))
            node = parent_node


        if failed_up:
            return None

        # if we found the root, we need
        # to check for query boundaries
        left_nei_pos = query_start-len(prefix_builder)
        if left_nei_pos >= 0 and not query[left_nei_pos].isspace():
            return None

        prefix = prefix_builder[::-1][:-1]

        return QueryUpResult(prefix=prefix, jumps=our_jumps)


    def _query_down(self, node: TrieNode, query: str, query_start: int, jumps: list[str], initial_jumps: list[str]) -> list[PlayWord]:
        results = []

        def dfs_down(node: TrieNode, jumps: list[str], prefix: PlayWord, query_index:int):
            nonlocal results

            if node.terminal and jumps != initial_jumps:
                results.append(prefix)

            query_index += 1
            if query_index >= len(query):
                return

            query_letter = query[query_index]


            for edge_letter, next_node_idx in node.edges.items():
                if not fulfills_query(edge_letter, query_letter):
                    continue

                new_jumps = jumps.copy()
                jmp_letter = edge_letter
                if query_letter.isspace():
                    jmp_letter = get_jump_letter(edge_letter, jumps)
                    if jmp_letter is None:
                        continue

                    new_jumps.remove(jmp_letter)

                play_letter = PlayLetter(letter=jmp_letter, wildcard_letter=edge_letter)
                new_prefix  = prefix + [play_letter]
                next_node = self.nodes[next_node_idx]
                dfs_down(next_node, new_jumps, new_prefix, query_index)


        dfs_down(node, jumps, [], query_start)

        # check for boundaries with query
        valid_results = []

        for suffix in results:
            right_nei_idx = query_start + len(suffix) + 1

            if right_nei_idx >= len(query) or query[right_nei_idx].isspace():
                valid_results.append(suffix)

        return valid_results




    def query(self, qu: str, jumps: str|list[str]) -> list[QueryResult]:
        """Query the trie"""

        # support both " " and "." for empty space
        qu = qu.replace(".", " ")
        starts = self._find_starts(qu)

        if len(starts) == 0:
            # TODO: this is an empty query (first word)
            pass

        if isinstance(jumps, str):
            jumps = list(jumps)

        all_results = []

        for start in starts:
            starting_letter = qu[start]

            if starting_letter not in self.node_tracker:
                continue

            nodes = self.node_tracker[starting_letter]

            for start_node in nodes:
                node = self.nodes[start_node]

                result_up = self._query_up(node, qu, start, jumps)
                
                if result_up is None:
                    continue

                prefix = result_up.prefix
                remaining_jumps = result_up.jumps

                node = self.nodes[start_node]
                results = self._query_down(node, qu, start, remaining_jumps, jumps)


                for suffix in results:
                    word = prefix + [PlayLetter(letter=qu[start])] + suffix
                    all_results.append(QueryResult(start-len(prefix), word))


        all_results = list(set(all_results))

        if False:
            print()
            print(f"-------- {len(all_results):5d} RESULTS     --------")
            print()

            print()
            print(qu.replace(" ", "."), "\t\tAvailable letters:", ''.join(sorted(jumps)))
            for qr in all_results:
                real_word = "".join(pl.real_letter for pl in qr.word)
                play_word = "".join(pl.letter for pl in qr.word)

                t = " " * qr.start_index + play_word
                print(t, end=" "*(len(qu) - len(t)))

                if "*" in play_word:
                    print(f"\t({real_word})", end="")

                print()


        return all_results




    def __str__(self):
        return pprint.pformat(self.nodes)



def create_greek_trie():
    t = Trie()

    t0 = time.time()
    with open("wordlist.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            t.add(line)

    diff = time.time() - t0
    print(f"Creating trie took {diff:.2f}s")

    return t

if __name__ == "__main__":
    T = create_greek_trie()


