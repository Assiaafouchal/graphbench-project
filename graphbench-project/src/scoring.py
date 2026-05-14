def violation_score(invariants):

    """
    Score temporaire simple
    """

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