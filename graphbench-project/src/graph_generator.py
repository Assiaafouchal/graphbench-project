import networkx as nx
import random


def generate_random_graph(n=10, p=0.3):

    G = nx.erdos_renyi_graph(n, p)

    # Assurer la connexité
    while not nx.is_connected(G):
        G = nx.erdos_renyi_graph(n, p)

    return G