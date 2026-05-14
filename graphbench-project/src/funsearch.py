# ============================================================
# funsearch.py
# ============================================================

import random

# ============================================================

def heuristic_v1(inv):

    return (

        inv["density"] * 50
        + inv["triangles"]
    )

# ============================================================

def heuristic_v2(inv):

    return (

        inv["Delta"] * 5
        + inv["avg"]
    )

# ============================================================

def heuristic_v3(inv):

    return (

        inv["triangles"] * 2
        + inv["density"] * 100
    )

# ============================================================

HEURISTICS = [

    heuristic_v1,
    heuristic_v2,
    heuristic_v3
]

# ============================================================

def generate_heuristic():

    return random.choice(
        HEURISTICS
    )

# ============================================================

def mutate_heuristic():

    return random.choice(
        HEURISTICS
    )

# ============================================================

def evaluate_heuristic(h, inv):

    try:

        return h(inv)

    except:

        return -9999