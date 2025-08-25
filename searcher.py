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
class QueryResult:
    start_index: int
    word: str

    def __hash__(self):
        return hash(f"{self.start_index}{self.word}")

class Trie:

    def __init__(self):
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
        current = self.nodes[0] # root

        for letter in word:
            if letter not in current.edges:
                self.create_node(letter, current.index)

            current = self.nodes[current.edges[letter]]


        # mark the final node as terminal
        current.terminal = True


    def query(self, qu: str, jumps: str) -> list[QueryResult]:
        starts = []
        qu = qu.replace(".", " ")
        cur_entry = -1
        for i, l in enumerate(qu):
            if not l.isspace():
                cur_entry = i
            else:
                if cur_entry != -1:
                    starts.append(cur_entry)
                cur_entry = -1

        if cur_entry != -1:
            starts.append(cur_entry)


        def debug_print_q_starts(q, s):
            qu_p = q.replace(' ', '.')
            points = [' '] * len(qu_p)
            for entry in s:
                points[entry] = '^'

            points_s = ''.join(points)

            print(qu_p)
            print(points_s)


        def get_jump_letter(letter_to_get: str, jumps: list[str]) -> str|None:
            """Return the letter used to jump to `letter_to_get`, else None"""
            if letter_to_get in jumps:
                return letter_to_get

            elif "*" in jumps:
                return "*"

            else:
                return None


        all_results = []

        for start in starts:
            starting_letter = qu[start]

            if starting_letter not in self.node_tracker:
                continue

            nodes = self.node_tracker[starting_letter]

            for start_node in nodes:
                node = self.nodes[start_node]

                # prune big branches we wont fit
                if node.depth > start + 1:
                    continue

                our_jumps = list(jumps)

                # first walk up
                failed_up = False
                query_index = start
                prefix_builder = [node.letter]

                while node.parent != 0:
                    query_index -= 1
                    parent_node = self.nodes[node.parent]

                    # if out of bounds of query, stop searching
                    if query_index < 0:
                        failed_up = True
                        break


                    query_letter = qu[query_index]
                    # if query has another fixed letter up and we
                    # do not match, stop searching
                    if not query_letter.isspace() and query_letter != parent_node.letter:
                        failed_up = True
                        break

                    # if next query up is space, we should just have
                    # an available jump
                    jmp = parent_node.letter
                    if query_letter.isspace():
                        jmp = get_jump_letter(parent_node.letter, our_jumps)
                        if jmp is None:
                            failed_up = True
                            break

                        our_jumps.remove(jmp)


                    prefix_builder.append(jmp)
                    node = parent_node


                if failed_up:
                    continue

                # if we found the root, we need
                # to check for query boundaries
                left_nei_pos = start-len(prefix_builder)
                if left_nei_pos >= 0 and not qu[left_nei_pos].isspace():
                    continue

                prefix = "".join(prefix_builder[::-1])[:-1]

                # now check going down (dfs)
                results = []
                def dfs_down(node: TrieNode, jumps: list[str], prefix: str, query_index:int):
                    nonlocal results
                    # prefix += node.letter

                    if node.terminal:
                        results.append(prefix)

                    query_index += 1
                    if query_index >= len(qu):
                        return

                    query_letter = qu[query_index]


                    def fulfills_query(letter: str, query_letter: str):
                        return query_letter.isspace() or letter == query_letter # or letter == '*'

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

                        next_node = self.nodes[next_node_idx]
                        dfs_down(next_node, new_jumps, prefix+jmp_letter, query_index)



                node = self.nodes[start_node]
                query_index = start
                dfs_down(node, our_jumps, "", query_index)

                for sufix in results:
                    # check for boundaries with query
                    right_nei_idx = start + len(sufix) + 1
                    if right_nei_idx >= len(qu) or qu[right_nei_idx].isspace():
                        word = prefix + qu[query_index] + sufix
                        all_results.append(QueryResult(start-len(prefix), word))


        all_results = list(set(all_results))

        print()
        print(f"-------- {len(all_results):5d} RESULTS -------")
        print()

        print()
        print(qu.replace(" ", "."), "\t\tAvailable letters:", jumps)
        for qr in all_results:
            print(" " * qr.start_index + qr.word)


        return all_results







    def __str__(self):
        return pprint.pformat(self.nodes)



t = Trie()

if 1:
    t0 = time.time()
    with open("wordlist.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            t.add(line)

    diff = time.time() - t0
    print(f"Creating trie took {diff:.2f}s")
else:
    t.add("testing")
    t.add("ping")
    t.add("est")
    t.add("test")
    t.query("   t   ", "tttteeeessiiing")
