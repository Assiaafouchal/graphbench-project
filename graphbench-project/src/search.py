import copy
import random

from mutations import (
    add_random_edge,
    remove_random_edge,
    add_random_node
)

from invariants import compute_invariants
from scoring import violation_score


def mutate_graph(G):

    mutations = [
        add_random_edge,
        remove_random_edge,
        add_random_node
    ]

    mutation = random.choice(mutations)

    return mutation(G)


def local_search(initial_graph, iterations=100):

    best_graph = copy.deepcopy(initial_graph)

    best_invariants = compute_invariants(best_graph)

    best_score = violation_score(best_invariants)

    print("\nScore initial :", best_score)

    for i in range(iterations):

        candidate = copy.deepcopy(best_graph)

        candidate = mutate_graph(candidate)

        invariants = compute_invariants(candidate)

        score = violation_score(invariants)

        if score > best_score:

            best_graph = candidate
            best_score = score
            best_invariants = invariants

            print(f"Nouvelle amélioration à l'itération {i}")
            print("Score :", best_score)

    return best_graph, best_score, best_invariants