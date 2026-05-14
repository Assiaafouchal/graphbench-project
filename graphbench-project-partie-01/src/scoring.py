import math


def violation_score(invariants):

    if invariants["diam"] == float("inf"):
        return -99999

    if invariants["rad"] == float("inf"):
        return -99999

    delta = invariants["delta"]
    Delta = invariants["Delta"]
    diam = invariants["diam"]
    triangles = invariants["triangles"]
    density = invariants["density"]
    n = invariants["n"]

    score = (
        4 * Delta
        - 2 * delta
        + 2.5 * diam
        + 0.7 * triangles
        + 8 * density
        - 0.1 * n
    )

    return score