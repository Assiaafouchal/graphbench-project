"""FunSearch — évolution automatique de la fonction de score via un LLM (Anthropic).

Architecture :
  1. Un pool de fonctions de score est initialisé avec BASE_HEURISTIC.
  2. À chaque round, le LLM reçoit les meilleures fonctions du pool
     et génère une nouvelle variante.
  3. La variante est évaluée sur un sous-ensemble de graphes.
  4. Les meilleures fonctions sont conservées dans le pool.
  5. La meilleure fonction globale est retournée après n_rounds rounds.
"""

import anthropic

# ---------------------------------------------------------------------------
# Fonction de base (point de départ de l'évolution)
# ---------------------------------------------------------------------------

BASE_HEURISTIC = '''def heuristic_score(G, invariants, conjecture):
    """
    G          : graphe NetworkX
    invariants : dictionnaire des invariants calculés
    conjecture : objet Conjecture avec méthode violation(invariants)
    retourne un score numérique à maximiser
    """
    violation = conjecture.violation(invariants)
    if violation is None:
        return -99999.0

    n = invariants.get("n", 0)
    m = invariants.get("m", 0)
    diam = invariants.get("diam", 0) if invariants.get("diam") != float("inf") else 0
    Delta = invariants.get("Delta", 0)
    triangles = invariants.get("triangles", 0)
    density = 2 * m / (n * (n - 1)) if n > 1 else 0

    return (
        10.0 * violation
        + 0.3 * diam
        + 0.2 * Delta
        + 0.1 * triangles
        - 0.05 * n
        - 0.2 * abs(density - 0.5)
    )
'''

# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

def _build_prompt(best_functions):
    """Construct the LLM prompt from the top functions in the pool."""
    examples = "\n\n".join(
        f"# Exemple {i + 1} (score moyen : {score:.4f})\n{code}"
        for i, (score, code) in enumerate(best_functions)
    )
    return f"""Tu es un expert en optimisation combinatoire et théorie des graphes.

Voici les meilleures fonctions de score heuristique actuelles pour réfuter des conjectures sur les graphes. Chaque fonction retourne un score à maximiser ; un score positif correspond à un contre-exemple valide.

{examples}

La fonction a la signature :
    def heuristic_score(G, invariants, conjecture)

où :
- G : graphe NetworkX
- invariants : dict avec les clés n, m, diam, rad, delta, Delta, avg, density,
  triangles, omega, gamma, total_dom, alpha, ind_dom, tau, mu, kappa,
  kappa_prime, lambda2, proximity, remoteness, largest_eigen,
  largest_dist_eigen, randic, zagreb1, zagreb2
- conjecture : objet avec méthode violation(invariants) → float | None
  (positif = contre-exemple trouvé, None = invariant manquant)

Génère UNE SEULE nouvelle fonction Python améliorée nommée exactement
`heuristic_score`. Elle doit guider la recherche vers des graphes qui violent
les conjectures. Tu peux combiner des invariants, ajouter des bonus/pénalités,
t'inspirer des exemples. Ne génère que le code Python, sans explication.
Commence directement par `def heuristic_score`."""


def _extract_code(text):
    """Extract the Python function code from the LLM response."""
    # Handle markdown code fences
    if "```python" in text:
        start = text.index("```python") + 9
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start) if "```" in text[start:] else len(text)
        text = text[start:end].strip()

    if "def heuristic_score" not in text:
        return None

    idx = text.index("def heuristic_score")
    return text[idx:].strip()


def compile_heuristic(code_str):
    """Compile code_str and return the heuristic_score function, or None."""
    try:
        namespace = {}
        exec(compile(code_str, "<funsearch>", "exec"), namespace)
        fn = namespace.get("heuristic_score")
        if callable(fn):
            return fn
    except Exception:
        pass
    return None


def evaluate_heuristic(code_str, sample_data):
    """Evaluate a heuristic on sample (G, invariants, conjecture) tuples.

    Returns the average score over the sample.
    """
    fn = compile_heuristic(code_str)
    if fn is None:
        return -99999.0

    total = 0.0
    count = 0
    for G, inv, conj in sample_data:
        try:
            s = fn(G, inv, conj)
            if s is not None and s not in (float("inf"), float("-inf")):
                total += s
                count += 1
        except Exception:
            total -= 100.0
            count += 1

    return total / count if count > 0 else -99999.0


# ---------------------------------------------------------------------------
# LLM interaction
# ---------------------------------------------------------------------------

def generate_heuristic(best_functions):
    """Ask Claude to generate a new heuristic based on the best ones.

    Returns the code string, or None on failure.
    """
    client = anthropic.Anthropic()
    prompt = _build_prompt(best_functions)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_code(response.content[0].text)
    except Exception as e:
        print(f"  [FunSearch] Erreur LLM : {e}")
        return None


# ---------------------------------------------------------------------------
# Boucle FunSearch principale
# ---------------------------------------------------------------------------

def funsearch_loop(benchmark, sample_data, n_rounds=5, pool_size=4):
    """Evolve the scoring heuristic using an LLM.

    Args:
        benchmark    : list of Conjecture objects (used for context only)
        sample_data  : list of (G, invariants, conjecture) for evaluation
        n_rounds     : number of LLM-evolution rounds
        pool_size    : max functions to keep in the pool

    Returns:
        (best_code, best_fn) where best_fn is the compiled callable
    """
    base_score = evaluate_heuristic(BASE_HEURISTIC, sample_data)
    pool = [(base_score, BASE_HEURISTIC)]

    print(f"\n[FunSearch] Démarrage — score initial : {base_score:.4f}")
    print(f"[FunSearch] {n_rounds} rounds, pool de {pool_size} fonctions\n")

    for round_idx in range(n_rounds):
        print(f"[FunSearch] Round {round_idx + 1}/{n_rounds}")

        top = sorted(pool, reverse=True)[:2]
        new_code = generate_heuristic(top)

        if new_code:
            new_score = evaluate_heuristic(new_code, sample_data)
            pool.append((new_score, new_code))
            print(f"  Nouvelle variante → score : {new_score:.4f}")
        else:
            print("  Pas de nouvelle variante (échec LLM)")

        pool.sort(reverse=True)
        pool = pool[:pool_size]
        print(f"  Meilleur score pool : {pool[0][0]:.4f}")

    best_score, best_code = pool[0]
    print(f"\n[FunSearch] Meilleure fonction (score : {best_score:.4f})")
    print("-" * 50)
    print(best_code)
    print("-" * 50)

    return best_code, compile_heuristic(best_code)
