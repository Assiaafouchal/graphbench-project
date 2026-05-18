import networkx as nx
import numpy as np

# Seuils au-delà desquels on utilise des approximations rapides
_CLIQUE_MAX_N = 18      # nx.find_cliques exponentiel au-delà
_CONNECTIVITY_MAX_N = 30  # node_connectivity / edge_connectivity lents au-delà
_EIGEN_MAX_N = 50       # calcul valeurs propres distance raisonnable
_MATCHING_MAX_N = 40    # max_weight_matching O(n³) — approx au-delà


def compute_invariants(G):
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n == 0:
        return {"n": 0, "m": 0}

    degrees = [d for _, d in G.degree()]
    deg = dict(G.degree())

    inv = {
        "n": n,
        "m": m,
        "delta": min(degrees),
        "Delta": max(degrees),
        "avg": sum(degrees) / n,
        "density": nx.density(G),
    }

    # --- Connectivity-dependent invariants ---
    if nx.is_connected(G):
        inv["diam"] = nx.diameter(G)
        inv["rad"] = nx.radius(G)

        lengths = dict(nx.all_pairs_shortest_path_length(G))
        avg_dists = [
            sum(lengths[v][u] for u in G.nodes() if u != v) / (n - 1)
            if n > 1 else 0.0
            for v in G.nodes()
        ]
        inv["proximity"] = min(avg_dists)
        inv["remoteness"] = max(avg_dists)

        try:
            # Utilise numpy dense eigensolver — plus fiable que l'itératif scipy
            L = nx.laplacian_matrix(G).toarray()
            eigs = np.linalg.eigvalsh(L)
            inv["lambda2"] = float(eigs[1]) if len(eigs) > 1 else 0.0
        except Exception:
            inv["lambda2"] = 0.0

        # Connectivité : coûteuse — approx par delta pour les grands graphes
        if n <= _CONNECTIVITY_MAX_N:
            inv["kappa"] = nx.node_connectivity(G)
            inv["kappa_prime"] = nx.edge_connectivity(G)
        else:
            inv["kappa"] = inv["delta"]        # borne inférieure
            inv["kappa_prime"] = inv["delta"]  # borne inférieure

        # Valeur propre distance : O(n³) — saut pour grands graphes
        if n <= _EIGEN_MAX_N:
            try:
                D = nx.floyd_warshall_numpy(G)
                inv["largest_dist_eigen"] = float(np.linalg.eigvalsh(D)[-1])
            except Exception:
                inv["largest_dist_eigen"] = 0.0
        else:
            inv["largest_dist_eigen"] = float(inv["diam"])  # approximation grossière
    else:
        inv["diam"] = float("inf")
        inv["rad"] = float("inf")
        inv["proximity"] = float("inf")
        inv["remoteness"] = float("inf")
        inv["lambda2"] = 0.0
        inv["kappa"] = 0
        inv["kappa_prime"] = 0
        inv["largest_dist_eigen"] = float("inf")

    # --- Triangles & clustering ---
    inv["triangles"] = sum(nx.triangles(G).values()) // 3
    inv["clustering"] = nx.average_clustering(G)

    # --- Clique number : exponentiel → approx pour grands graphes ---
    if n <= _CLIQUE_MAX_N:
        try:
            cliques = list(nx.find_cliques(G))
            inv["omega"] = max(len(c) for c in cliques) if cliques else 1
        except Exception:
            inv["omega"] = _greedy_clique_approx(G)
    else:
        inv["omega"] = _greedy_clique_approx(G)

    # --- Independence number : greedy rapide ---
    inv["alpha"] = _greedy_independence(G)

    # --- Vertex cover: tau = n - alpha ---
    inv["tau"] = n - inv["alpha"]

    # --- Matching number ---
    try:
        if n <= _MATCHING_MAX_N:
            matching = nx.max_weight_matching(G, maxcardinality=True)
            inv["mu"] = len(matching)
        else:
            inv["mu"] = n // 2  # borne supérieure approchée
    except Exception:
        inv["mu"] = 0

    # --- Domination & total domination (greedy) ---
    inv["gamma"] = _greedy_domination(G)
    inv["total_dom"] = _greedy_total_domination(G)
    inv["ind_dom"] = _greedy_independent_domination(G)

    # --- Largest adjacency eigenvalue ---
    if n <= _EIGEN_MAX_N:
        try:
            A = nx.to_numpy_array(G)
            inv["largest_eigen"] = float(np.linalg.eigvalsh(A)[-1])
        except Exception:
            inv["largest_eigen"] = float(inv["Delta"])
    else:
        inv["largest_eigen"] = float(inv["Delta"])  # approximation

    # --- Randic index ---
    try:
        inv["randic"] = sum(
            1.0 / (deg[u] * deg[v]) ** 0.5
            for u, v in G.edges()
            if deg[u] > 0 and deg[v] > 0
        )
    except Exception:
        inv["randic"] = 0.0

    # --- Zagreb indices ---
    inv["zagreb1"] = sum(d ** 2 for d in degrees)
    inv["zagreb2"] = sum(deg[u] * deg[v] for u, v in G.edges())

    return inv


# ---------------------------------------------------------------------------
# Greedy helper functions (toutes en O(n·Δ) — rapides)
# ---------------------------------------------------------------------------

def _greedy_clique_approx(G):
    """Greedy clique approximation: start from highest-degree node."""
    best = 1
    for start in sorted(G.nodes(), key=lambda v: G.degree(v), reverse=True)[:5]:
        clique = {start}
        candidates = set(G.neighbors(start))
        while candidates:
            v = max(candidates, key=lambda u: len(set(G.neighbors(u)) & candidates))
            clique.add(v)
            candidates &= set(G.neighbors(v))
        best = max(best, len(clique))
    return best


def _greedy_domination(G):
    nodes = set(G.nodes())
    dominated = set()
    dom_set = set()
    while dominated != nodes:
        best = max(
            (v for v in nodes if v not in dom_set),
            key=lambda v: len((set(G.neighbors(v)) | {v}) - dominated),
            default=None,
        )
        if best is None:
            break
        dom_set.add(best)
        dominated.add(best)
        dominated.update(G.neighbors(best))
    return len(dom_set)


def _greedy_total_domination(G):
    if G.number_of_nodes() == 0 or G.number_of_edges() == 0:
        return 0
    nodes = set(G.nodes())
    dominated = set()
    dom_set = set()
    while dominated != nodes:
        candidates = [v for v in nodes if v not in dom_set]
        if not candidates:
            break
        best = max(candidates, key=lambda v: len(set(G.neighbors(v)) - dominated))
        dom_set.add(best)
        dominated.update(G.neighbors(best))
    return len(dom_set)


def _greedy_independent_domination(G):
    nodes = sorted(G.nodes(), key=lambda v: G.degree(v))
    ind_dom_set = set()
    excluded = set()
    for v in nodes:
        if v not in excluded and v not in ind_dom_set:
            ind_dom_set.add(v)
            excluded.update(G.neighbors(v))
    return len(ind_dom_set)


def _greedy_independence(G):
    nodes = sorted(G.nodes(), key=lambda v: G.degree(v))
    ind_set = set()
    excluded = set()
    for v in nodes:
        if v not in excluded:
            ind_set.add(v)
            excluded.update(G.neighbors(v))
    return len(ind_set)
