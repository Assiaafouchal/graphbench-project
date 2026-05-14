import networkx as nx


def compute_invariants(G):

    invariants = {}

    invariants["n"] = G.number_of_nodes()
    invariants["m"] = G.number_of_edges()

    degrees = [d for _, d in G.degree()]

    invariants["delta"] = min(degrees)
    invariants["Delta"] = max(degrees)
    invariants["avg"] = sum(degrees) / len(degrees)

    if nx.is_connected(G):
        invariants["diam"] = nx.diameter(G)
        invariants["rad"] = nx.radius(G)
    else:
        invariants["diam"] = float("inf")
        invariants["rad"] = float("inf")

    invariants["density"] = nx.density(G)

    triangles = sum(nx.triangles(G).values()) // 3
    invariants["triangles"] = triangles

    invariants["clustering"] = nx.average_clustering(G)

    return invariants