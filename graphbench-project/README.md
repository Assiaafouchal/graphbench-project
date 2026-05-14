# GraphBench Project

Structure minimale du projet pour lancer des benchmarks sur des graphes.

Organisation:

- `benchmark/benchmark.xlsx`: fichier de données de benchmark (placeholder).
- `results/`: sortie des expériences.
- `src/`: code source Python.

Fichiers principaux dans `src/`:
- `main.py`: point d'entrée.
- `benchmark_loader.py`, `graph_generator.py`, `invariants.py`, `scoring.py`, `mutations.py`, `repair.py`, `search.py`, `utils.py`, `config.py`.

Installation minimale:

```
pip install -r requirements.txt
```

Usage:

```
python src/main.py
```

Licence: MIT (à adapter)
