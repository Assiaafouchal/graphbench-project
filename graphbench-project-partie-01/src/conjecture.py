from fractions import Fraction
import ast



def parse_coefficient(coeff_str):

    try:

        values = ast.literal_eval(coeff_str)

        if len(values) != 1:
            return None

        return float(Fraction(values[0]))

    except:
        return None



def compute_violation(conjecture, invariants):

    x_name = conjecture["X"]
    y_name = conjecture["Y"]

    sign = conjecture["Sign"]

    coeff_raw = conjecture["Coefficients"]
    intercept_raw = conjecture["Intercept"]

    coeff = parse_coefficient(coeff_raw)

    if coeff is None:
        return None

    try:
        intercept = float(intercept_raw)
    except:
        intercept = 0.0

    mapping = {
        "order": "n",
        "size": "m",
        "diameter": "diam",
        "radius": "rad",
        "minimum_degree": "delta",
        "maximum_degree": "Delta",
        "average_degree": "avg",
        "triangle_number": "triangles",
        "density": "density"
    }

    if x_name not in mapping:
        return None

    if y_name not in mapping:
        return None

    x = invariants.get(mapping[x_name], 0)
    y = invariants.get(mapping[y_name], 0)

    if x == float("inf") or y == float("inf"):
        return None

    rhs = coeff * y + intercept

    if sign == "<=":
        violation = x - rhs

    elif sign == ">=":
        violation = rhs - x

    else:
        return None

    return violation