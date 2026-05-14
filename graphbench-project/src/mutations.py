# ============================================================
# mutations.py
# ============================================================

import random
import networkx as nx

# ============================================================

def mutate_graph(G):

    mutations = [

        add_random_edge,
        remove_random_edge,
        add_random_node,
        densify_graph
    ]

    mutation = random.choice(
        mutations
    )

    return mutation(G)

# ============================================================

def add_random_edge(G):

    nodes = list(G.nodes())

    for _ in range(20):

        u = random.choice(nodes)
        v = random.choice(nodes)

        if u != v and not G.has_edge(u, v):

            G.add_edge(u, v)

            return G

    return G

# ============================================================

def remove_random_edge(G):

    edges = list(G.edges())

    if len(edges) == 0:

        return G

    edge = random.choice(edges)

    G.remove_edge(*edge)

    if not nx.is_connected(G):

        G.add_edge(*edge)

    return G

# ============================================================

def add_random_node(G):

    new_node = max(G.nodes()) + 1

    G.add_node(new_node)

    targets = random.sample(
        list(G.nodes()),
        k=min(3, len(G.nodes()))
    )

    for t in targets:

        if t != new_node:

            G.add_edge(new_node, t)

    return G

# ============================================================

def densify_graph(G):

    nodes = list(G.nodes())

    for _ in range(5):

        u = random.choice(nodes)
        v = random.choice(nodes)

        if u != v:

            G.add_edge(u, v)

    return G