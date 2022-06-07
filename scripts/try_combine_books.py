import networkx as nx
import graphviz
import math
import random
import os

class Book:
    def __init__(self, content):
        self.content = content
        self.name = None

    def __hash__(self):
        return hash(self.content)

    def get_overlap_length(self, next):
        i = 0
        max_overlap = min(len(self.content), len(next.content))
        for j in range(1, max_overlap):
            if self.content[-j:] == next.content[:j]:
                i = j
        return i

    def concat_merge_overlap(self, next, expect_overlap=True):
        overlap = self.get_overlap_length(next)
        if expect_overlap and overlap == 0:
            raise Exception('Expected overlap.')
        return Book(self.content + next.content[overlap:])

    def __eq__(self, other):
        return self.content == other.content

    def __contains__(self, other):
        if isinstance(other, str):
            return other in self.content
        elif isinstance(other, Book):
            return other.content in self.content
        else:
            raise Exception('Invalid type.')

    def __len__(self):
        return len(self.content)

    def get_all_substrings(self):
        for i in range(len(self.content)):
            for j in range(i+1, len(self.content)):
                yield self.content[i:j]

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name or hex(hash(self))

class Library:
    def __init__(self, books=[]):
        self.books = books.copy()

    def add(self, book):
        if not isinstance(book, Book):
            raise Exception('Not a book.')
        self.books.append(book)

    def get_unique(self):
        new_library = Library()
        for i, first_book in enumerate(self.books):
            is_unique = True
            for j, second_book in enumerate(self.books):
                if i == j:
                    continue

                if first_book in second_book:
                    is_unique = False
                    break

            if is_unique:
                new_library.add(first_book)

        return new_library

    def __iter__(self):
        return iter(self.books)

    def __len__(self):
        return len(self.books)

    def try_assign_names(self, max_length=24):
        for i in range(1, max_length):
            names = set()
            names2 = list()
            for book in self.books:
                names.add(book.content[:i])
            if len(names) == len(self.books):
                for b in self.books:
                    b.set_name(b.content[:i])
                break

    def save(self, filename):
        with open(filename, 'w') as file:
            file.write('\n'.join([book.content for book in self.books]))

def read_library(filename):
    library = Library()
    with open(filename, 'r') as file:
        for line in file:
            library.add(Book(line.strip()))
    return library

def make_prefix_suffix_overlap_graph(library, min_overlap=1):
    G = nx.DiGraph()

    for book in library:
        G.add_node(book)

    for first_book in library:
        for second_book in library:
            if first_book == second_book:
                continue

            overlap = first_book.get_overlap_length(second_book)
            if overlap >= min_overlap:
                G.add_edge(first_book, second_book, overlap=overlap)

    return G

def get_edges_ordered_by_overlap_descending(G):
    return list(sorted(G.edges.data(), key=lambda x: -x[2]['overlap']))

def get_edges_random_order(G):
    v = list(G.edges.data())
    random.shuffle(v)
    return v

def get_edges_random_order_somewhat_weighted(G, weight_dumpening=1.0):
    v = list(G.edges.data())
    v.sort(key=lambda x: -(x[2]['overlap'] ** weight_dumpening) * random.random())
    return v

def get_edges_random_order_weighted(G, weight_dumpening=1.0):
    v = list(G.edges.data())
    v.sort(key=lambda x: -(random.random() ** (1.0 / (x[2]['overlap'] ** weight_dumpening))))
    return v

def get_edges_random_order_weighted_hard_split(G, weight_dumpening=1.0, split_min=3):
    '''
    Keeps two partitions.
    '''
    def key(x):
        return -(random.random() ** (1.0 / (x[2]['overlap'] ** weight_dumpening)))

    vall = list(G.edges.data())
    vlow = [v for v in vall if v[2]['overlap'] < split_min]
    vhigh = [v for v in vall if v[2]['overlap'] >= split_min]
    vlow.sort(key=lambda x: key(x))
    vhigh.sort(key=lambda x: key(x))
    return vlow + vhigh

def decompose_to_paths_greedy(G, edges_getter=get_edges_ordered_by_overlap_descending):
    paths = []
    for a, b, attr in edges_getter(G):
        overlap = attr['overlap']
        path_with_a = None
        path_with_b = None
        for i, path in enumerate(paths):
            if a in path:
                path_with_a = i
            if b in path:
                path_with_b = i

        if path_with_a is not None and path_with_b is not None and path_with_a == path_with_b:
            continue

        if path_with_a is None and path_with_b is None:
            P = nx.DiGraph()
            P.add_node(a)
            P.add_node(b)
            P.add_edge(a, b, overlap=overlap)
            paths.append(P)

        elif path_with_a is None and path_with_b is not None:
            P = paths[path_with_b]
            if P.in_degree(b) == 0:
                P.add_node(a)
                P.add_edge(a, b, overlap=overlap)

        elif path_with_a is not None and path_with_b is None:
            P = paths[path_with_a]
            if P.out_degree(a) == 0:
                P.add_node(b)
                P.add_edge(a, b, overlap=overlap)

        elif path_with_a is not None and path_with_b is not None:
            P = paths[path_with_a]
            Q = paths[path_with_b]
            if P.out_degree(a) == 0 and Q.in_degree(b) == 0:
                R = nx.compose(P, Q)
                R.add_edge(a, b, overlap=overlap)
                paths.append(R)
                paths.remove(P)
                paths.remove(Q)

    for book in G.nodes:
        is_lone = True
        for path in paths:
            if book in path:
                is_lone = False
                break
        if is_lone:
            P = nx.DiGraph()
            P.add_node(book)
            paths.append(P)

    return paths

def to_graphviz(G):
    f = graphviz.Digraph()
    max_overlap = 0
    for a, b, attr in G.edges.data():
        max_overlap = max(max_overlap, attr['overlap'])

    for node in G.nodes:
        f.node(node.get_name())
    for a, b, attr in G.edges.data():
        overlap = attr['overlap']
        opacity = min(max(int(255 * math.pow(overlap/max_overlap, 0.5)), 10), 255)
        color = '#000000' + hex(opacity)[2:]
        f.edge(a.get_name(), b.get_name(), label=str(overlap), color=color)
    return f

def path_to_book(path):
    book = None
    for node in nx.topological_sort(path):
        if book is None:
            book = node
        else:
            book = book.concat_merge_overlap(node)
    return book

def paths_to_library(paths):
    new_library = Library()
    for path in paths:
        new_library.add(path_to_book(path))
    return new_library

def paths_to_graph(paths):
    G = nx.DiGraph()
    for p in paths:
        G = nx.compose(G, p)
    return G

RENDER_OVERLAP_GRAPHS = False
DO_GREEDY_DECOMPOSITION = False
DO_RANDOMIZED_DECOMPOSITION = True
NUM_RANDOMIZED_ITERATIONS = 10000
RUN_N_TIMES = 100
METRIC = 'num_paths'
#METRIC = 'sum_of_overlaps' # Conjecture: greedy descending by overlap the best?

# What min overlap to consider? 1? 2? 3?
# There are some books that overlap by only one digit,
# but when included these edges dominate.
# NOTE: It is possible that there are books that are consecutive but do not overlap at all.
#       In such case though we have no way to know that until we decode the language.
MIN_OVERLAP = 1

# Assuming a random distribution of digits (not actually true) we can expect on average
# around (50 unique books) 50 * 49 / 10^3 == 2.45 edges with overlap of 3 digits,
# this is acceptable. Using 4 as a threshold would push it down to ~0.245.
MIN_OVERLAP_CONSIDERED_NOT_COINCIDENTAL = 1

def sum_of_overlaps(paths):
    total = 0
    for path in paths:
        for a, b, attr in path.edges.data():
            total += attr['overlap']
    return total

def make_suffix_for_paths(paths):
    suffix_parts = []
    ordered_paths = sorted(paths, key=lambda x: -len(x))
    for path in ordered_paths:
        path_length = len(path)
        combined_book_length = len(path_to_book(path))
        suffix_parts.append(f'{combined_book_length}[{path_length}]')
    return f'#{len(paths)}_' + '_'.join(suffix_parts)

def main():
    os.makedirs('out/graphs', exist_ok=True)
    os.makedirs('out/books', exist_ok=True)

    library = read_library('books_raw.txt')
    print(f'Whole library size: {len(library)}')

    unique_library = library.get_unique()
    unique_library.try_assign_names()
    print(f'Unique library size: {len(unique_library)}')

    if RENDER_OVERLAP_GRAPHS:
        for i in range(1, 16):
            G = make_prefix_suffix_overlap_graph(unique_library, i)
            print(f'Minimum {i} overlap length:', G)
            to_graphviz(G).render(outfile=f'overlap_min_{i}.svg', format='svg', engine='dot', directory='out/graphs')

    G = make_prefix_suffix_overlap_graph(unique_library, MIN_OVERLAP)

    # TODO: Try to find a hamiltionian path? no good already existing implementations.
    #       Maybe would be easier to check if it even exists?
    #       Probably easiest to convert to a SAT problem and use existing solvers...

    if DO_GREEDY_DECOMPOSITION:
        paths_greedy = decompose_to_paths_greedy(G)
        print('Greedy decomposition paths:', len(paths_greedy))
        new_library = paths_to_library(paths_greedy)
        suffix = make_suffix_for_paths(paths_greedy)
        new_library.save(f'out/books/books_combined_greedy_{suffix}.txt')
        to_graphviz(paths_to_graph(paths_greedy)).render(outfile=f'out/graphs/greedy_decomposition_{suffix}.svg', format='svg', engine='dot')

    if DO_RANDOMIZED_DECOMPOSITION:
        best_paths = None
        for j in range(NUM_RANDOMIZED_ITERATIONS):
            # TODO: Maybe a more clever randomization that takes number of in/out edges into account?
            paths = decompose_to_paths_greedy(G, lambda G: get_edges_random_order_weighted_hard_split(G, 0.75, MIN_OVERLAP_CONSIDERED_NOT_COINCIDENTAL))
            if best_paths is None:
                best_paths = paths
            elif METRIC == 'sum_of_overlaps' and sum_of_overlaps(best_paths) < sum_of_overlaps(paths):
                best_paths = paths
            elif METRIC == 'num_paths' and len(best_paths) > len(paths):
                best_paths = paths

            if (j + 1) % 10 == 0:
                if METRIC == 'sum_of_overlaps':
                    print(f'Iter {j+1}, Best {sum_of_overlaps(best_paths)}, Current {sum_of_overlaps(paths)}')
                elif METRIC == 'num_paths':
                    print(f'Iter {j+1}, Best {len(best_paths)}, Current {len(paths)}')

        print('best_paths:', len(best_paths))
        new_library = paths_to_library(best_paths)
        suffix = make_suffix_for_paths(best_paths)
        new_library.save(f'out/books/books_combined_{suffix}.txt')
        gv = to_graphviz(paths_to_graph(best_paths))
        gv.render(outfile=f'out/graphs/decomposition_{suffix}.svg', format='svg', engine='dot')

if __name__ == '__main__':
    for i in range(RUN_N_TIMES):
        main()
