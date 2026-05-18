def violation_score(invariants, conjecture):
    """Return the violation of the conjecture for this graph.

    Positive value means the conjecture is violated (counterexample found).
    Returns a large negative value when the graph is invalid (disconnected, etc.).
    """
    if invariants.get("diam") == float("inf"):
        return -99999.0
    if invariants.get("rad") == float("inf"):
        return -99999.0

    v = conjecture.violation(invariants)
    if v is None:
        return -99999.0
    return v
