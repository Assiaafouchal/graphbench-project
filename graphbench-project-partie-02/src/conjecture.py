from fractions import Fraction
import ast


# Mapping: benchmark column name → internal invariant key (used in compute_invariants)
INVARIANT_MAP = {
    "order": "n",
    "size": "m",
    "diameter": "diam",
    "radius": "rad",
    "minimum_degree": "delta",
    "maximum_degree": "Delta",
    "average_degree": "avg",
    "density": "density",
    "triangle_number": "triangles",
    "clique_number": "omega",
    "domination_number": "gamma",
    "total_domination_number": "total_dom",
    "independence_number": "alpha",
    "independent_domination_number": "ind_dom",
    "vertex_cover_number": "tau",
    "matching_number": "mu",
    "vertex_connectivity": "kappa",
    "edge_connectivity": "kappa_prime",
    "second_smallest_laplace_eigenvalue": "lambda2",
    "proximity": "proximity",
    "remoteness": "remoteness",
    "largest_eigenvalue": "largest_eigen",
    "largest_distance_eigenvalue": "largest_dist_eigen",
    "randic_index": "randic",
    "first_zagreb_index": "zagreb1",
    "second_zagreb_index": "zagreb2",
}


class Conjecture:
    """Represents one conjecture from the benchmark.

    Conjecture form: Y(G) {sign} f(X(G))
    where f(x) = intercept + c1*x + c2*x^2 + ... + cd*x^d
    """

    def __init__(self, x_name, y_name, sign, coefficients, intercept,
                 graph_class="connected", cid=""):
        self.x_name = x_name          # benchmark column name for X
        self.y_name = y_name          # benchmark column name for Y
        self.sign = sign              # "<=" or ">="
        self.coefficients = coefficients  # list of floats [c1, c2, ..., cd]
        self.intercept = intercept    # float
        self.graph_class = graph_class
        self.id = cid

    def _eval_polynomial(self, x):
        """Compute f(x) = intercept + c1*x + c2*x^2 + ..."""
        result = self.intercept
        for i, c in enumerate(self.coefficients):
            result += c * (x ** (i + 1))
        return result

    def violation(self, invariants):
        """Compute the violation score.

        For Y <= f(X): violation = Y - f(X)   (positive → counterexample)
        For Y >= f(X): violation = f(X) - Y   (positive → counterexample)
        Returns None if a required invariant is unavailable or infinite.
        """
        x_key = INVARIANT_MAP.get(self.x_name)
        y_key = INVARIANT_MAP.get(self.y_name)

        if x_key is None or y_key is None:
            return None

        x = invariants.get(x_key)
        y = invariants.get(y_key)

        if x is None or y is None:
            return None
        if x == float("inf") or y == float("inf"):
            return None

        fx = self._eval_polynomial(x)

        if self.sign == "<=":
            return float(y) - fx       # positive means Y > f(X) → conjecture violated
        elif self.sign == ">=":
            return fx - float(y)       # positive means f(X) > Y → conjecture violated
        return None

    def __repr__(self):
        return (f"Conjecture({self.id}: {self.y_name} {self.sign} "
                f"f({self.x_name}), class={self.graph_class})")


def parse_conjecture_row(row):
    """Parse a pandas DataFrame row into a Conjecture object."""
    # Parse polynomial coefficients
    try:
        coeff_list = ast.literal_eval(str(row["Coefficients"]))
        coefficients = [float(Fraction(str(c))) for c in coeff_list]
    except Exception:
        coefficients = [1.0]

    # Parse intercept
    try:
        intercept = float(Fraction(str(row["Intercept"])))
    except Exception:
        intercept = 0.0

    # Parse graph class from Subgroup field (e.g. "['connected', 'tree']")
    try:
        subgroup = ast.literal_eval(str(row["Subgroup"]))
        if "tree" in subgroup:
            graph_class = "tree"
        elif "claw_free" in subgroup:
            graph_class = "claw_free"
        elif "bipartite" in subgroup:
            graph_class = "bipartite"
        elif "planar" in subgroup:
            graph_class = "planar"
        else:
            graph_class = "connected"
    except Exception:
        graph_class = "connected"

    return Conjecture(
        x_name=str(row["X"]),
        y_name=str(row["Y"]),
        sign=str(row["Sign"]),
        coefficients=coefficients,
        intercept=intercept,
        graph_class=graph_class,
        cid=str(row.get("Conjecture ID", "")),
    )
