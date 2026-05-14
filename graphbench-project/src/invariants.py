import networkx as nx


def compute_invariants(G):

    invariants = {}

    # Nombre de sommets
    invariants["n"] = G.number_of_nodes()

    # Nombre d'arêtes
    invariants["m"] = G.number_of_edges()

    # Liste des degrés
    degrees = [d for _, d in G.degree()]

    # Degré minimum
    invariants["delta"] = min(degrees)

    # Degré maximum
    invariants["Delta"] = max(degrees)

    # Degré moyen
    invariants["avg"] = sum(degrees) / len(degrees)

    # Diamètre
    if nx.is_connected(G):
        invariants["diam"] = nx.diameter(G)
    else:
        invariants["diam"] = float("inf")

    # Rayon
    if nx.is_connected(G):
        invariants["rad"] = nx.radius(G)
    else:
        invariants["rad"] = float("inf")

    # Densité
    invariants["density"] = nx.density(G)

    # Nombre de triangles
    triangles = sum(nx.triangles(G).values()) // 3
    invariants["triangles"] = triangles

    return invariants