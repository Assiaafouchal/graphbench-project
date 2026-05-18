import random
import networkx as nx

MAX_N = 25   # taille maximale autorisée pour le graphe


def _new_node_id(G):
    """Return a fresh integer node ID not already in G."""
    existing = set(G.nodes())
    i = 0
    while i in existing:
        i += 1
    return i


def mutate_graph(G):
    mutations = [
        add_random_edge,
        remove_random_edge,
        add_random_node,
        densify_graph,
        subdivide_random_edge,
        add_leaf,
    ]
    return random.choice(mutations)(G)


def add_random_edge(G):
    nodes = list(G.nodes())
    for _ in range(20):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v and not G.has_edge(u, v):
            G.add_edge(u, v)
            return G
    return G


def remove_random_edge(G):
    edges = list(G.edges())
    if not edges:
        return G
    edge = random.choice(edges)
    G.remove_edge(*edge)
    if not nx.is_connected(G):
        G.add_edge(*edge)
    return G


def add_random_node(G):
    if G.number_of_nodes() >= MAX_N:
        return add_random_edge(G)   # fallback : ajouter une arête plutôt
    new_node = _new_node_id(G)
    G.add_node(new_node)
    targets = random.sample(list(G.nodes()), k=min(2, len(G.nodes())))
    for t in targets:
        if t != new_node:
            G.add_edge(new_node, t)
    return G


def densify_graph(G):
    nodes = list(G.nodes())
    for _ in range(3):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v:
            G.add_edge(u, v)
    return G


def subdivide_random_edge(G):
    if G.number_of_nodes() >= MAX_N:
        return add_random_edge(G)   # fallback
    edges = list(G.edges())
    if not edges:
        return G
    u, v = random.choice(edges)
    G.remove_edge(u, v)
    new_node = _new_node_id(G)
    G.add_node(new_node)
    G.add_edge(u, new_node)
    G.add_edge(new_node, v)
    return G


def add_leaf(G):
    if G.number_of_nodes() >= MAX_N:
        return add_random_edge(G)   # fallback
    nodes = list(G.nodes())
    if not nodes:
        return G
    parent = random.choice(nodes)
    new_node = _new_node_id(G)
    G.add_node(new_node)
    G.add_edge(parent, new_node)
    return G
