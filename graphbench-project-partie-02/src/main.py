import time
import csv
import os
import random
import networkx as nx

from benchmark_loader import load_benchmark
from graph_generator import generate_initial_graph
from invariants import compute_invariants
from search import find_counterexample
from funsearch import funsearch_loop
from config import BENCHMARK_FILE

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TIME_LIMIT = 60        # secondes par conjecture
BEAM_WIDTH = 10
INITIAL_N = 15
FUNSEARCH_ROUNDS = 4   # rounds d'évolution LLM
POOL_SIZE = 4          # taille du pool de fonctions
SAMPLE_SIZE = 8        # nombre d'évaluations pour FunSearch

# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------
benchmark = load_benchmark(BENCHMARK_FILE)

# ---------------------------------------------------------------------------
# Phase 1 : construire les données d'évaluation pour FunSearch
# (petits graphes + conjectures variées tirés aléatoirement)
# ---------------------------------------------------------------------------
print("\n[Phase 1] Construction des données d'évaluation pour FunSearch...")

sample_conjectures = random.sample(benchmark, min(SAMPLE_SIZE, len(benchmark)))
sample_data = []
for conj in sample_conjectures:
    G = generate_initial_graph(12, conj.graph_class)
    inv = compute_invariants(G)
    sample_data.append((G, inv, conj))

print(f"  {len(sample_data)} paires (graphe, conjecture) générées")

# ---------------------------------------------------------------------------
# Phase 2 : FunSearch — évolution de la fonction de score
# ---------------------------------------------------------------------------
print("\n[Phase 2] Lancement de FunSearch...")

best_code, best_score_fn = funsearch_loop(
    benchmark,
    sample_data,
    n_rounds=FUNSEARCH_ROUNDS,
    pool_size=POOL_SIZE,
)

# Fallback si FunSearch échoue
if best_score_fn is None:
    print("[FunSearch] Fallback : utilisation du score de violation brut")

# ---------------------------------------------------------------------------
# Phase 3 : benchmark complet avec la meilleure heuristique
# ---------------------------------------------------------------------------
print(f"\n[Phase 3] Benchmark complet ({len(benchmark)} conjectures)...\n")

total_refuted = 0
total_cost = 0.0
times_found = []
results = []

for i, conjecture in enumerate(benchmark):
    print(f"\n{'='*65}")
    print(f"Conjecture {i+1}/{len(benchmark)} | ID : {conjecture.id}")
    print(f"Classe : {conjecture.graph_class}")
    print(f"Relation : {conjecture.y_name} {conjecture.sign} f({conjecture.x_name})")
    print(f"{'='*65}")

    start = time.time()

    best_graph, best_score, best_inv, found = find_counterexample(
        conjecture,
        graph_class=conjecture.graph_class,
        beam_width=BEAM_WIDTH,
        time_limit=TIME_LIMIT,
        score_fn=best_score_fn,
    )

    elapsed = time.time() - start

    if found and best_graph is not None:
        total_refuted += 1
        total_cost += elapsed
        times_found.append(elapsed)

        g6 = nx.to_graph6_bytes(best_graph).decode().strip()
        print(f"\n  CONTRE-EXEMPLE TROUVÉ en {elapsed:.2f}s")
        print(f"  graph6 : {g6}")
        print(f"  Violation : {best_score:.6f}")
        if best_inv:
            print(f"  n={best_inv.get('n')}, m={best_inv.get('m')}")

        results.append({"id": conjecture.id, "found": True,
                        "elapsed": elapsed, "score": best_score, "g6": g6})
    else:
        total_cost += 120.0
        print(f"\n  Aucun contre-exemple (meilleur score : {best_score:.4f})")
        results.append({"id": conjecture.id, "found": False,
                        "elapsed": elapsed, "score": best_score})

# ---------------------------------------------------------------------------
# Résultats finaux
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("RÉSULTATS FINAUX")
print("=" * 70)
print(f"Conjectures réfutées : {total_refuted}/{len(benchmark)}")
print(f"Score total (coût)   : {round(total_cost, 1)}")
if times_found:
    avg = sum(times_found) / len(times_found)
    print(f"Temps moyen (trouvés): {round(avg, 2)}s")
print("=" * 70)

# ---------------------------------------------------------------------------
# Sauvegarde des résultats en CSV
# ---------------------------------------------------------------------------
results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(results_dir, exist_ok=True)

csv_path = os.path.join(results_dir, "results.csv")
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["conjecture_id", "found", "elapsed_s", "violation_score", "graph6"])
    writer.writeheader()
    for r in results:
        writer.writerow({
            "conjecture_id": r["id"],
            "found":         r["found"],
            "elapsed_s":     round(r["elapsed"], 4),
            "violation_score": round(r["score"], 6),
            "graph6":        r.get("g6", ""),
        })

print(f"\nRésultats CSV   : {csv_path}")
