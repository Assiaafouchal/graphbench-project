import sys
import time
import csv
import os
import networkx as nx

from benchmark_loader import load_benchmark
from search import find_counterexample
from config import BENCHMARK_FILE

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TIME_LIMIT = 60       # secondes par conjecture
BEAM_WIDTH = 15

# ---------------------------------------------------------------------------
# Reprise : python main.py --start 24  → reprend à la conjecture 24
# ---------------------------------------------------------------------------
start_from = 0
if "--start" in sys.argv:
    idx = sys.argv.index("--start")
    try:
        start_from = int(sys.argv[idx + 1]) - 1   # converti en index 0-based
    except (IndexError, ValueError):
        print("Usage: python main.py [--start N]  (N = numéro de conjecture, commence à 1)")
        sys.exit(1)

# ---------------------------------------------------------------------------
# Chargement du benchmark
# ---------------------------------------------------------------------------
benchmark = load_benchmark(BENCHMARK_FILE)

total_refuted = 0
total_cost = 0.0
times_found = []
results = []

if start_from > 0:
    print(f"\nReprise depuis la conjecture {start_from + 1}/{len(benchmark)}")
    total_cost = start_from * 120.0
else:
    print(f"\nLancement sur {len(benchmark)} conjectures (limite : {TIME_LIMIT}s chacune)")

print(f"Benchmark : {BENCHMARK_FILE}\n")

# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------
for i, conjecture in enumerate(benchmark):
    if i < start_from:
        continue

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
    )

    elapsed = time.time() - start

    if found and best_graph is not None:
        total_refuted += 1
        total_cost += elapsed
        times_found.append(elapsed)

        g6 = nx.to_graph6_bytes(best_graph).decode().strip()

        print(f"\n  CONTRE-EXEMPLE TROUVÉ en {elapsed:.2f}s")
        print(f"  graph6 : {g6}")
        print(f"  Violation (score) : {best_score:.6f}")
        if best_inv:
            from conjecture import INVARIANT_MAP
            x_key = INVARIANT_MAP.get(conjecture.x_name, conjecture.x_name)
            y_key = INVARIANT_MAP.get(conjecture.y_name, conjecture.y_name)
            print(f"  n={best_inv.get('n')}, m={best_inv.get('m')}")
            print(f"  {conjecture.y_name} ({y_key}) = {best_inv.get(y_key, 'N/A')}")
            print(f"  {conjecture.x_name} ({x_key}) = {best_inv.get(x_key, 'N/A')}")

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
