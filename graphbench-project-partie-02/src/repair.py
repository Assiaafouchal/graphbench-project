import random
import itertools
import networkx as nx

_MAX_CLAW_CHECKS = 30   # combinaisons max vérifiées par nœud (évite O(Δ³))


def repair_graph(G, graph_class="connected"):
    if G.number_of_nodes() == 0:
        return G
    if graph_class == "tree":
        return _repair_tree(G)
    elif graph_class == "claw_free":
        G = _repair_connected(G)
        return _repair_claw_free(G)
    elif graph_class == "bipartite":
        return _repair_bipartite(G)
    elif graph_class == "planar":
        G = _repair_connected(G)
        return _repair_planar(G)
    else:
        return _repair_connected(G)


def _repair_connected(G):
    if nx.is_connected(G):
        return G
    components = list(nx.connected_components(G))
    for i in range(len(components) - 1):
        u = random.choice(list(components[i]))
        v = random.choice(list(components[i + 1]))
        G.add_edge(u, v)
    return G


def _repair_tree(G):
    G = _repair_connected(G)
    return nx.minimum_spanning_tree(G)


def _repair_claw_free(G, max_iterations=50):
    """Supprime des arêtes pour éliminer les griffes K_{1,3}.

    Limité à _MAX_CLAW_CHECKS triplets par nœud par itération
    pour éviter O(Δ³) sur des graphes denses.
    """
    for _ in range(max_iterations):
        claw_found = False
        nodes = list(G.nodes())
        random.shuffle(nodes)          # ordre aléatoire pour diversité
        for v in nodes:
            nbrs = list(G.neighbors(v))
            if len(nbrs) < 3:
                continue
            # Limiter le nombre de triplets vérifiés
            combos = list(itertools.combinations(nbrs, 3))
            if len(combos) > _MAX_CLAW_CHECKS:
                combos = random.sample(combos, _MAX_CLAW_CHECKS)
            for a, b, c in combos:
                if not G.has_edge(a, b) and not G.has_edge(b, c) and not G.has_edge(a, c):
                    to_remove = min([(v, a), (v, b), (v, c)],
                                    key=lambda e: G.degree(e[1]))
                    u, w = to_remove
                    G.remove_edge(u, w)
                    if not nx.is_connected(G):
                        G.add_edge(u, w)
                    claw_found = True
                    break
            if claw_found:
                break
        if not claw_found:
            break
    return G


def _repair_bipartite(G):
    if G.number_of_nodes() == 0:
        return G
    color = {}
    to_remove = []
    for start in G.nodes():
        if start in color:
            continue
        color[start] = 0
        queue = [start]
        while queue:
            v = queue.pop()
            for u in G.neighbors(v):
                if u not in color:
                    color[u] = 1 - color[v]
                    queue.append(u)
                elif color[u] == color[v]:
                    to_remove.append((v, u))
    for e in to_remove:
        if G.has_edge(*e):
            G.remove_edge(*e)
    return G


def _repair_planar(G):
    while not nx.is_planar(G):
        edges = list(G.edges())
        if not edges:
            break
        e = random.choice(edges)
        G.remove_edge(*e)
        if not nx.is_connected(G):
            G.add_edge(*e)
    return G
