from benchmark_loader import load_benchmark

benchmark = load_benchmark("benchmark/benchmark.xlsx")
from graph_generator import generate_random_graph

G = generate_random_graph()

print("Nombre de sommets :", G.number_of_nodes())
print("Nombre d'arêtes :", G.number_of_edges())

from invariants import compute_invariants

inv = compute_invariants(G)

print(inv)
from scoring import violation_score

score = violation_score(inv)

print("Score :", score)

from mutations import (
    add_random_edge,
    remove_random_edge,
    add_random_node
)

print("\n--- AVANT MUTATION ---")
print("Sommets :", G.number_of_nodes())
print("Arêtes :", G.number_of_edges())

G = add_random_edge(G)
G = remove_random_edge(G)
G = add_random_node(G)

print("\n--- APRÈS MUTATION ---")
print("Sommets :", G.number_of_nodes())
print("Arêtes :", G.number_of_edges())
from search import local_search

best_graph, best_score, best_inv = local_search(G)

print("\n===== MEILLEUR GRAPHE =====")
print("Score final :", best_score)
print(best_inv)