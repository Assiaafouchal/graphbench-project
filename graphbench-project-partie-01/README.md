# GraphBench — Partie 1 : Heuristique simple

Projet M1 MIAGE — Réfutation automatique de conjectures en théorie des graphes.

## Structure du projet

```
graphbench-project-partie-01/
├── src/                  # Code source
│   ├── main.py           # Point d'entrée principal
│   ├── search.py         # Recherche en 3 phases (Atlas → canonique → beam search)
│   ├── invariants.py     # Calcul des invariants (n, m, diam, α, γ, µ, κ, …)
│   ├── conjecture.py     # Classe Conjecture + calcul de violation
│   ├── mutations.py      # Mutations locales de graphes
│   ├── repair.py         # Réparation de la classe (connexe, arbre, sans-griffe…)
│   ├── graph_generator.py# Générateurs par classe de graphes
│   ├── scoring.py        # Fonction de score = violation
│   ├── benchmark_loader.py
│   └── config.py
├── benchmark/
│   └── benchmark.xlsx    # 100 conjectures à réfuter
├── experiments/          # Logs bruts des expériences
├── results/
│   └── results.csv       # Résultats (généré automatiquement)
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
cd src
python main.py
```

Les résultats sont automatiquement sauvegardés dans `results/results.csv`.

## Algorithme — 3 phases par conjecture

1. **Phase Atlas** : test exhaustif de tous les graphes connexes de taille ≤ 7 (Graph Atlas de NetworkX), y compris K₁.
2. **Phase canonique** : batterie de graphes extrémaux (chemins, étoiles, cycles, graphes complets, bipartis, spiders, caterpillars, lollipops, barbell, …) jusqu'à n ≤ 25.
3. **Beam search multi-démarrage** : mutations locales + relances aléatoires dans la limite de temps restante (60 s total).

## Mutations implémentées

- Ajout / suppression d'arête
- Ajout de sommet
- Subdivision d'arête
- Ajout de feuille
- Densification locale

## Réparation par classe

| Classe | Stratégie |
|---|---|
| connected | Reconnexion des composantes |
| tree | Arbre couvrant |
| claw_free | Suppression des griffes K₁,₃ |
| bipartite | Recoloration BFS 2-coloring |
| planar | Suppression d'arêtes jusqu'à planarité |
