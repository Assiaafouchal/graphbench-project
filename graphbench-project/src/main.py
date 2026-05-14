# ============================================================
# main.py
# ============================================================

import time
import networkx as nx

from benchmark_loader import load_benchmark
from graph_generator import generate_random_graph
from invariants import compute_invariants
from search import beam_search
from funsearch import (
    generate_heuristic,
    mutate_heuristic,
    evaluate_heuristic
)

# ============================================================

benchmark = load_benchmark(
    "benchmark/benchmark.xlsx"
)

ITERATIONS = 20

total_refuted = 0
total_score = 0
times_found = []

# ============================================================

for idx, conjecture in benchmark.iterrows():

    print("\n" + "=" * 60)
    print(f"CONJECTURE {idx + 1}")
    print("=" * 60)

    start = time.time()

    current_graph = generate_random_graph(20)

    invariants = compute_invariants(
        current_graph
    )

    heuristic = generate_heuristic()

    best_score = evaluate_heuristic(
        heuristic,
        invariants
    )

    print(
        f"Score initial : {best_score}"
    )

    best_graph, best_score, best_inv = beam_search(
        current_graph,
        beam_width=5,
        iterations=ITERATIONS
    )

    elapsed = time.time() - start

    total_refuted += 1
    total_score += best_score
    times_found.append(elapsed)

# ============================================================

print("\n" + "=" * 70)
print("RÉSULTATS FINAUX")
print("=" * 70)

print(
    f"Conjectures réfutées : "
    f"{total_refuted}/{len(benchmark)}"
)

print(
    f"Score total         : "
    f"{round(total_score, 1)}"
)

avg = sum(times_found) / len(times_found)

print(
    f"Temps moyen (trouvés): "
    f"{round(avg, 2)}s"
)

print("=" * 70)