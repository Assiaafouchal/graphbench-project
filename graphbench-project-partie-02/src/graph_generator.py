import random
import networkx as nx


def generate_initial_graph(n=15, graph_class="connected"):
    """Generate a random graph belonging to graph_class."""
    if graph_class == "tree":
        return _tree_graph(n)
    elif graph_class == "claw_free":
        return _claw_free_graph(n)
    elif graph_class == "bipartite":
        return _bipartite_graph(n)
    elif graph_class == "planar":
        return _planar_graph(n)
    else:
        return _connected_graph(n)


# Keep the old name for backward compatibility
def generate_random_graph(n=15, p=0.4):
    return _connected_graph(n, p)


# ---------------------------------------------------------------------------

def _connected_graph(n, p=None):
    if n <= 1:
        G = nx.Graph(); G.add_node(0); return G
    if n == 2:
        return nx.path_graph(2)
    if p is None:
        p = random.uniform(0.3, 0.6)
    k_ws = min(n - 1, max(2, random.randint(2, 6)))  # k ≤ n pour Watts-Strogatz
    generators = [
        lambda: nx.erdos_renyi_graph(n, p),
        lambda: nx.barabasi_albert_graph(n, min(n - 1, random.randint(1, 4))),
        lambda: nx.watts_strogatz_graph(n, k_ws, random.uniform(0.1, 0.5)),
    ]
    G = random.choice(generators)()
    while not nx.is_connected(G):
        G = random.choice(generators)()
    return G


def _tree_graph(n):
    if n <= 1:
        G = nx.Graph()
        G.add_node(0)
        return G
    if n == 2:
        return nx.path_graph(2)
    # Random labeled tree via Prüfer sequence (works on all networkx versions)
    prufer = [random.randint(0, n - 1) for _ in range(n - 2)]
    return nx.from_prufer_sequence(prufer)


def _claw_free_graph(n):
    # Line graphs are always claw-free; relabel nodes to integers
    m = max(n // 2, 2)
    H = _connected_graph(m)
    L = nx.line_graph(H)
    if L.number_of_nodes() == 0:
        return nx.cycle_graph(max(n, 3))
    return nx.convert_node_labels_to_integers(L)


def _bipartite_graph(n):
    n1 = n // 2
    n2 = n - n1
    p = random.uniform(0.3, 0.7)
    G = nx.bipartite.random_graph(n1, n2, p)
    while not nx.is_connected(G):
        G = nx.bipartite.random_graph(n1, n2, p)
    return G


def _planar_graph(n):
    rows = max(2, int(n ** 0.5))
    cols = max(2, (n + rows - 1) // rows)
    G = nx.triangular_lattice_graph(rows, cols)
    G = nx.convert_node_labels_to_integers(G)
    return G
