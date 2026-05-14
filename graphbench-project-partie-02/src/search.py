# ============================================================
# search.py
# ============================================================

import copy
import random

from mutations import (
    mutate_graph
)

from invariants import compute_invariants
from scoring import violation_score

# ============================================================

def beam_search(
    initial_graph,
    beam_width=5,
    iterations=20
):

    beam = [copy.deepcopy(initial_graph)]

    best_graph = initial_graph
    best_score = -999999
    best_inv = None

    # ========================================================

    for iteration in range(iterations):

        candidates = []

        for graph in beam:

            for _ in range(3):

                candidate = copy.deepcopy(graph)

                candidate = mutate_graph(
                    candidate
                )

                inv = compute_invariants(
                    candidate
                )

                score = violation_score(
                    inv
                )

                candidates.append(
                    (
                        score,
                        candidate,
                        inv
                    )
                )

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        beam = [
            c[1]
            for c in candidates[:beam_width]
        ]

        if candidates[0][0] > best_score:

            best_score = candidates[0][0]
            best_graph = candidates[0][1]
            best_inv = candidates[0][2]

            print(
                f"Itération {iteration} | "
                f"Nouveau meilleur score : "
                f"{best_score}"
            )

    return (
        best_graph,
        best_score,
        best_inv
    )