# GraphBench — Partie 2 : Architecture FunSearch

Projet M1 MIAGE — Réfutation automatique de conjectures via évolution de la fonction de score par LLM.

## Structure du projet

```
graphbench-project-partie-02/
├── src/
│   ├── main.py           # Point d'entrée : FunSearch puis benchmark complet
│   ├── funsearch.py      # Boucle FunSearch (LLM Anthropic Claude)
│   ├── search.py         # Recherche en 3 phases (Atlas → canonique → beam search)
│   ├── invariants.py     # Calcul des invariants
│   ├── conjecture.py     # Classe Conjecture + violation
│   ├── mutations.py      # Mutations locales
│   ├── repair.py         # Réparation par classe
│   ├── graph_generator.py
│   ├── scoring.py
│   ├── benchmark_loader.py
│   └── config.py
├── benchmark/
│   └── benchmark.xlsx
├── experiments/
├── results/
│   └── results.csv
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # requis pour FunSearch
```

## Lancement

```bash
cd src
python main.py
```

## Architecture FunSearch

1. **Initialisation** : fonction de base `heuristic_score(G, invariants, conjecture)`.
2. **Évaluation** : score moyen sur un échantillon de (graphe, conjecture).
3. **Génération LLM** : Claude reçoit les meilleures fonctions et propose une variante améliorée.
4. **Sélection** : les `pool_size` meilleures fonctions sont conservées.
5. **Répétition** : `n_rounds` rounds d'évolution.
6. **Application** : la meilleure fonction guide le beam search sur les 100 conjectures.

## Forme de la fonction générée

```python
def heuristic_score(G, invariants, conjecture):
    violation = conjecture.violation(invariants)
    # bonus et pénalités sur les invariants
    return score
```
