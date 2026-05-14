import random
import networkx as nx


def add_random_edge(G):

    nodes = list(G.nodes())

    u = random.choice(nodes)
    v = random.choice(nodes)

    if u != v:
        G.add_edge(u, v)

    return G


def remove_random_edge(G):

    if G.number_of_edges() == 0:
        return G

    edge = random.choice(list(G.edges()))

    G.remove_edge(*edge)

    if not nx.is_connected(G):
        G.add_edge(*edge)

    return G


def add_random_node(G):

    new_node = max(G.nodes()) + 1

    G.add_node(new_node)

    target = random.choice(list(G.nodes()))

    G.add_edge(new_node, target)

    return G