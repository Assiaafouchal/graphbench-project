def violation_score(invariants):

    if invariants["diam"] == float("inf"):
        return -9999

    if invariants["rad"] == float("inf"):
        return -9999

    delta = invariants["delta"]
    Delta = invariants["Delta"]
    diam = invariants["diam"]
    triangles = invariants["triangles"]

    score = (
        Delta
        - delta
        + 0.5 * diam
        + 0.2 * triangles
    )

    return score