"""
search.py — Stratégie de recherche en 3 phases pour réfuter les conjectures.

Phase 1 : Vérification exhaustive de tous les graphes connexes du Graph Atlas (n ≤ 7).
Phase 2 : Batterie de graphes canoniques + extrémaux + spiders + powers.
Phase 3 : Beam search multi-démarrage avec relances et mutations diversifiées.
"""

import copy
import time
import random
import itertools

import networkx as nx

from mutations import mutate_graph
from invariants import compute_invariants
from scoring import violation_score
from repair import repair_graph
from graph_generator import generate_initial_graph


# ---------------------------------------------------------------------------
# Utilitaire interne
# ---------------------------------------------------------------------------

def _check_graph(G, conjecture):
    """Calcule (score, inv) pour G. Ne lève jamais d'exception."""
    try:
        inv = compute_invariants(G)
        score = violation_score(inv, conjecture)
        if score is None:
            score = -999999.0
        return float(score), inv
    except Exception:
        return -999999.0, None


def _is_claw_free(G):
    """Vérifie si G est sans griffe (K_{1,3}-free)."""
    for v in G.nodes():
        nbrs = list(G.neighbors(v))
        if len(nbrs) < 3:
            continue
        for a, b, c in itertools.combinations(nbrs, 3):
            if not G.has_edge(a, b) and not G.has_edge(b, c) and not G.has_edge(a, c):
                return False
    return True


def _class_ok(G, graph_class):
    """Retourne True si G respecte la contrainte de classe."""
    if not nx.is_connected(G):
        return False
    if graph_class == "tree":
        return nx.is_tree(G)
    if graph_class == "bipartite":
        return nx.is_bipartite(G)
    if graph_class == "planar":
        return nx.is_planar(G)
    if graph_class == "claw_free":
        return _is_claw_free(G)
    return True  # "connected"


# ---------------------------------------------------------------------------
# Phase 1 — Vérification exhaustive (Graph Atlas, n ≤ 7)
# ---------------------------------------------------------------------------

def _exhaustive_small_graphs(conjecture, graph_class, max_n=7):
    """Parcourt tous les graphes connexes de l'Atlas (n ≤ max_n).
    Inclut K_1 (n=1) — critique pour les conjectures impliquant proximity=0 / remoteness=0.
    Retourne (best_score, best_graph, best_inv, found).
    """
    best_score = -999999.0
    best_graph = None
    best_inv = None

    # ── Test de K_1 en premier (n=1, graphe à un seul sommet) ──────────────
    # Crucial pour les conjectures f(proximity) >= Y ou proximity >= f(X)
    # car proximity(K_1) = remoteness(K_1) = 0.
    K1 = nx.Graph()
    K1.add_node(0)
    if _class_ok(K1, graph_class):
        score, inv = _check_graph(K1, conjecture)
        if score > best_score:
            best_score, best_graph, best_inv = score, copy.deepcopy(K1), inv
        if score > 0:
            return best_score, best_graph, best_inv, True

    try:
        atlas = list(nx.graph_atlas_g())
    except Exception:
        return best_score, best_graph, best_inv, False

    for G in atlas:
        n = G.number_of_nodes()
        if n < 2 or n > max_n:
            continue
        if not _class_ok(G, graph_class):
            continue

        G = nx.convert_node_labels_to_integers(G)
        score, inv = _check_graph(G, conjecture)

        if score > best_score:
            best_score = score
            best_graph = copy.deepcopy(G)
            best_inv = inv

        if score > 0:
            return best_score, best_graph, best_inv, True

    return best_score, best_graph, best_inv, False


# ---------------------------------------------------------------------------
# Phase 2 — Batterie de graphes canoniques
# ---------------------------------------------------------------------------

def _build_spider(arm_lengths):
    """Spider graph : centre + bras de longueurs arm_lengths."""
    G = nx.Graph()
    center = 0
    G.add_node(center)
    nid = 1
    for arm_len in arm_lengths:
        prev = center
        for _ in range(arm_len):
            G.add_edge(prev, nid)
            prev = nid
            nid += 1
    return G


def _iter_canonical_graphs(graph_class, max_n=25):
    """Générateur de graphes canoniques extrémaux (du plus petit au plus grand)."""

    seen_sigs = set()

    def emit(G):
        if G is None:
            return None
        try:
            G = nx.convert_node_labels_to_integers(G)
        except Exception:
            return None
        if not _class_ok(G, graph_class):
            return None
        deg_seq = tuple(sorted(d for _, d in G.degree()))
        sig = (G.number_of_nodes(), G.number_of_edges(), deg_seq)
        if sig in seen_sigs:
            return None
        seen_sigs.add(sig)
        return G

    # ── Graphes classiques (chemin, étoile, cycle, complet, roue, biparti) ──
    for n in range(2, max_n + 1):
        builders = [
            lambda n=n: nx.path_graph(n),
            lambda n=n: nx.star_graph(n - 1) if n >= 2 else None,
            lambda n=n: nx.cycle_graph(n) if n >= 3 else None,
        ]
        if graph_class not in ("tree", "bipartite"):
            builders += [
                lambda n=n: nx.complete_graph(n),
                lambda n=n: nx.wheel_graph(n) if n >= 4 else None,
            ]
        for builder in builders:
            G = builder()
            if G is not None:
                G = emit(G)
                if G is not None:
                    yield G

        # Biparti complet K_{n1,n2}
        for n1 in range(1, n // 2 + 1):
            n2 = n - n1
            G = emit(nx.complete_bipartite_graph(n1, n2))
            if G is not None:
                yield G

        # Cocktail-party (K_n moins couplage parfait)
        if n >= 4 and n % 2 == 0 and graph_class not in ("tree", "bipartite"):
            G_cp = nx.complete_graph(n)
            for i in range(0, n, 2):
                if G_cp.has_edge(i, i + 1):
                    G_cp.remove_edge(i, i + 1)
            G = emit(G_cp)
            if G is not None:
                yield G

    # ── Spider graphs (centre + k bras de longueur variable) ────────────────
    # Clé pour γ_t, γ, α vs µ, τ — donne des violations que chemin/étoile ratent
    for k in range(2, 7):        # 2 à 6 bras
        for lengths in itertools.product(range(1, 7), repeat=k):
            n = 1 + sum(lengths)
            if n > max_n:
                continue
            G = emit(_build_spider(lengths))
            if G is not None:
                yield G

    # ── Caterpillar graphs (chemin central + feuilles pendantes) ─────────────
    for spine_len in range(2, 12):
        for leaf_count in range(1, 4):
            spine = list(range(spine_len))
            G = nx.path_graph(spine_len)
            nid = spine_len
            for v in spine:
                for _ in range(leaf_count):
                    G.add_edge(v, nid); nid += 1
            if G.number_of_nodes() <= max_n:
                G2 = emit(G)
                if G2 is not None:
                    yield G2

    # ── Lollipop graphs (K_k + chemin de longueur p) ─────────────────────────
    if graph_class not in ("tree", "bipartite"):
        for k in range(2, 7):
            for p in range(1, 6):
                if k + p <= max_n:
                    try:
                        G = emit(nx.lollipop_graph(k, p))
                        if G is not None:
                            yield G
                    except Exception:
                        pass

    # ── Barbell graphs (K_k + chemin + K_k) ──────────────────────────────────
    if graph_class not in ("tree", "bipartite"):
        for k in range(2, 5):
            for p in range(0, 6):
                if 2 * k + p <= max_n:
                    try:
                        G = emit(nx.barbell_graph(k, p))
                        if G is not None:
                            yield G
                    except Exception:
                        pass

    # ── Tadpole graphs (C_m + chemin P_n) ─────────────────────────────────────
    if graph_class not in ("bipartite",):
        for m in range(3, 8):
            for p in range(1, 6):
                if m + p <= max_n:
                    try:
                        G = emit(nx.tadpole_graph(m, p))
                        if G is not None:
                            yield G
                    except Exception:
                        pass

    # ── Double étoile S_{a,b} ────────────────────────────────────────────────
    for a in range(1, 9):
        for b in range(a, 9):
            if 2 + a + b > max_n:
                continue
            G = nx.Graph()
            G.add_edge(0, 1)
            nid = 2
            for _ in range(a):
                G.add_edge(0, nid); nid += 1
            for _ in range(b):
                G.add_edge(1, nid); nid += 1
            G = emit(G)
            if G is not None:
                yield G

    # ── Graphes de Turán T(n,r) ─────────────────────────────────────────────
    if graph_class not in ("tree", "bipartite"):
        for r in range(2, 6):
            for n in range(r, min(max_n + 1, 20)):
                try:
                    G = emit(nx.turan_graph(n, r))
                    if G is not None:
                        yield G
                except Exception:
                    pass

    # ── Puissances de cycles et de chemins (sans-griffe garantis) ───────────
    if graph_class in ("claw_free", "connected"):
        for n in range(4, min(max_n + 1, 22)):
            for power in (2, 3):
                try:
                    G = emit(nx.power(nx.cycle_graph(n), power))
                    if G is not None:
                        yield G
                except Exception:
                    pass
                try:
                    G = emit(nx.power(nx.path_graph(n), power))
                    if G is not None:
                        yield G
                except Exception:
                    pass

    # ── Graphes de lignes (toujours sans-griffe) ────────────────────────────
    if graph_class in ("claw_free", "connected"):
        for k in range(3, 9):
            for base_builder in [
                lambda k=k: nx.complete_graph(k),
                lambda k=k: nx.path_graph(k + 1),
                lambda k=k: nx.cycle_graph(k),
                lambda k=k: nx.star_graph(k),
                lambda k=k: nx.complete_bipartite_graph(k, k),
                lambda k=k: nx.complete_bipartite_graph(2, k),
            ]:
                try:
                    base = base_builder()
                    L = nx.line_graph(base)
                    L = nx.convert_node_labels_to_integers(L)
                    G = emit(L)
                    if G is not None:
                        yield G
                except Exception:
                    pass

    # ── Graphes Petersen et autres spéciaux ──────────────────────────────────
    for special in [nx.petersen_graph]:
        try:
            G = emit(special())
            if G is not None:
                yield G
        except Exception:
            pass

    # ── Grilles et treillis (bonne structure de distance) ───────────────────
    if graph_class in ("connected", "planar"):
        for r in range(2, 7):
            for c in range(2, 7):
                if (r * c) > max_n:
                    continue
                try:
                    G = emit(nx.grid_2d_graph(r, c))
                    if G is not None:
                        yield G
                except Exception:
                    pass

    # ── Graphes circulants (structure régulière variée) ──────────────────────
    if graph_class not in ("tree",):
        for n in range(4, min(max_n + 1, 18)):
            for offsets in [(1,), (1, 2), (1, 2, 3), (2, 3)]:
                if max(offsets) < n:
                    try:
                        G = emit(nx.circulant_graph(n, offsets))
                        if G is not None:
                            yield G
                    except Exception:
                        pass


def _canonical_battery(conjecture, graph_class, max_n=25, time_budget=20.0):
    """Teste les graphes canoniques dans la limite de time_budget secondes.
    Retourne (best_score, best_graph, best_inv, found).
    """
    best_score = -999999.0
    best_graph = None
    best_inv = None
    deadline = time.time() + time_budget

    for G in _iter_canonical_graphs(graph_class, max_n):
        if time.time() > deadline:
            break
        score, inv = _check_graph(G, conjecture)
        if score > best_score:
            best_score = score
            best_graph = copy.deepcopy(G)
            best_inv = inv
        if score > 0:
            return best_score, best_graph, best_inv, True

    return best_score, best_graph, best_inv, False


# ---------------------------------------------------------------------------
# Phase 3 — Beam search multi-démarrage
# ---------------------------------------------------------------------------

def beam_search(initial_graph, conjecture, graph_class="connected",
                beam_width=15, time_limit=60, score_fn=None):
    """Beam search avec relances aléatoires et tailles variées.
    Retourne (best_graph, best_score, best_inv, found_counterexample).
    """
    start_time = time.time()

    start_sizes = [4, 5, 6, 7, 8, 10, 12, 15, 18, 20]

    # Évaluation initiale
    best_score, best_inv = _check_graph(initial_graph, conjecture)
    best_graph = copy.deepcopy(initial_graph)
    found_counterexample = best_score > 0

    if found_counterexample:
        return best_graph, best_score, best_inv, True

    beam = [copy.deepcopy(initial_graph)]
    iteration = 0
    next_restart = time.time() + 7  # relance toutes les 7s (pas 10)

    # Mode intensif seulement si on a une violation réelle (> 0)
    # Sinon, on diversifie (relances aléatoires) pour trouver de nouveaux graphes
    intensive_mode = best_score > 0.05

    while time.time() - start_time < time_limit:
        now = time.time()

        # ── Relance périodique ──────────────────────────────────────────────
        if now >= next_restart:
            if intensive_mode:
                # Mode intensif : perturbations légères autour du meilleur
                new_g = copy.deepcopy(best_graph)
                for _ in range(random.randint(2, 5)):
                    new_g = mutate_graph(new_g)
                new_g = repair_graph(new_g, graph_class)
            else:
                # Mode diversification : nouveau graphe aléatoire
                n = random.choice(start_sizes)
                new_g = generate_initial_graph(n, graph_class)

                # Bonus : essayer le complémentaire si connexe
                if graph_class not in ("tree",) and random.random() < 0.3:
                    try:
                        comp = nx.complement(best_graph)
                        if nx.is_connected(comp):
                            comp_ok = repair_graph(
                                nx.convert_node_labels_to_integers(comp), graph_class
                            )
                            sc2, inv2 = _check_graph(comp_ok, conjecture)
                            if sc2 > best_score:
                                best_score, best_graph, best_inv = sc2, copy.deepcopy(comp_ok), inv2
                                if sc2 > 0:
                                    return best_graph, best_score, best_inv, True
                    except Exception:
                        pass

                # Essayer aussi un spider aléatoire pour classes tree/connected
                if graph_class in ("tree", "connected") and random.random() < 0.5:
                    k = random.randint(2, 6)
                    lengths = tuple(random.randint(1, 6) for _ in range(k))
                    spider = _build_spider(lengths)
                    spider = nx.convert_node_labels_to_integers(spider)
                    if spider.number_of_nodes() <= 30:
                        sc2, inv2 = _check_graph(spider, conjecture)
                        if sc2 > best_score:
                            best_score, best_graph, best_inv = sc2, copy.deepcopy(spider), inv2
                            if sc2 > 0:
                                return best_graph, best_score, best_inv, True
                        new_g = spider  # Utiliser spider comme point de départ

                # Essayer un graphe de plus grande taille pour les invariants de distance
                if random.random() < 0.3:
                    n_large = random.choice([20, 25, 30])
                    try:
                        new_g_large = generate_initial_graph(n_large, graph_class)
                        sc2, inv2 = _check_graph(new_g_large, conjecture)
                        if sc2 > best_score:
                            best_score, best_graph, best_inv = sc2, copy.deepcopy(new_g_large), inv2
                            if sc2 > 0:
                                return best_graph, best_score, best_inv, True
                    except Exception:
                        pass

            sc, inv = _check_graph(new_g, conjecture)
            if sc > best_score:
                best_score, best_graph, best_inv = sc, copy.deepcopy(new_g), inv
                elapsed = now - start_time
                print(f"  restart ({elapsed:.1f}s) | score : {best_score:.4f}")
                if sc > 0:
                    found_counterexample = True
                    break

            beam = [copy.deepcopy(best_graph), copy.deepcopy(new_g)]
            next_restart = now + 7
            intensive_mode = best_score > 0.05

        # ── Expansion du beam ───────────────────────────────────────────────
        candidates = []
        for graph in beam:
            for _ in range(8):
                candidate = copy.deepcopy(graph)
                k = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
                for _ in range(k):
                    candidate = mutate_graph(candidate)
                candidate = repair_graph(candidate, graph_class)

                if score_fn is not None:
                    try:
                        inv = compute_invariants(candidate)
                        score = score_fn(candidate, inv, conjecture)
                    except Exception:
                        score, inv = _check_graph(candidate, conjecture)
                else:
                    score, inv = _check_graph(candidate, conjecture)

                candidates.append((score, candidate, inv))

        if not candidates:
            break

        candidates.sort(key=lambda x: x[0], reverse=True)
        beam = [c[1] for c in candidates[:beam_width]]

        top_score = candidates[0][0]
        if top_score > best_score:
            best_score = top_score
            best_graph = candidates[0][1]
            best_inv = candidates[0][2]
            elapsed = time.time() - start_time
            print(f"  iter {iteration} ({elapsed:.1f}s) | score : {best_score:.4f}")
            intensive_mode = best_score > 0.05

        if best_score > 0:
            found_counterexample = True
            break

        iteration += 1

    return best_graph, best_score, best_inv, found_counterexample


# ---------------------------------------------------------------------------
# Point d'entrée principal
# ---------------------------------------------------------------------------

def find_counterexample(conjecture, graph_class="connected",
                        beam_width=15, time_limit=60, score_fn=None):
    """Recherche en 3 phases : exhaustif → canonique → beam search.
    Retourne (best_graph, best_score, best_inv, found).
    """
    start_time = time.time()
    best_score = -999999.0
    best_graph = None
    best_inv = None

    # ── Phase 1 : exhaustif Atlas (n ≤ 7) ──────────────────────────────────
    sc, g, inv, found = _exhaustive_small_graphs(conjecture, graph_class, max_n=7)
    if sc > best_score:
        best_score, best_graph, best_inv = sc, g, inv
    if found:
        elapsed = time.time() - start_time
        print(f"  [Atlas] trouvé en {elapsed:.2f}s | score : {best_score:.4f}")
        return best_graph, best_score, best_inv, True

    # ── Phase 2 : batterie canonique étendue (budget 8s max) ────────────────
    # On garde le budget court pour donner le maximum de temps au beam search
    phase2_budget = min(8.0, time_limit * 0.12)
    sc, g, inv, found = _canonical_battery(
        conjecture, graph_class, max_n=25, time_budget=phase2_budget
    )
    if sc > best_score:
        best_score, best_graph, best_inv = sc, g, inv
    if found:
        elapsed = time.time() - start_time
        print(f"  [Canon] trouvé en {elapsed:.2f}s | score : {best_score:.4f}")
        return best_graph, best_score, best_inv, True

    # ── Phase 3 : beam search multi-restart ─────────────────────────────────
    remaining = time_limit - (time.time() - start_time)
    if remaining > 2:
        initial = best_graph if best_graph is not None \
                  else generate_initial_graph(10, graph_class)
        bg, bs, bi, found = beam_search(
            initial, conjecture, graph_class,
            beam_width=beam_width,
            time_limit=remaining,
            score_fn=score_fn,
        )
        if bs > best_score or found:
            best_score, best_graph, best_inv = bs, bg, bi
            if found:
                return best_graph, best_score, best_inv, True

    return best_graph, best_score, best_inv, False
