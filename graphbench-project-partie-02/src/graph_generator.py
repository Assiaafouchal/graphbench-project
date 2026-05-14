import networkx as nx
import random


def generate_random_graph(n=20):

    generators = [

        erdos_graph,
        barabasi_graph,
        watts_graph,
        dense_graph
    ]

    generator = random.choice(generators)

    return generator(n)


# ==========================================

def erdos_graph(n):

    p = random.uniform(0.3, 0.7)

    G = nx.erdos_renyi_graph(n, p)

    while not nx.is_connected(G):

        G = nx.erdos_renyi_graph(n, p)

    return G


# ==========================================

def barabasi_graph(n):

    m = random.randint(2, 5)

    return nx.barabasi_albert_graph(n, m)


# ==========================================

def watts_graph(n):

    k = random.randint(2, 6)

    p = random.uniform(0.1, 0.5)

    return nx.watts_strogatz_graph(n, k, p)


# ==========================================

def dense_graph(n):

    p = random.uniform(0.6, 0.9)

    G = nx.erdos_renyi_graph(n, p)

    while not nx.is_connected(G):

        G = nx.erdos_renyi_graph(n, p)

    return G