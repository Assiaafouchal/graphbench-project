# Experiments

Ce dossier contient les résultats bruts des expériences.

## Lancer une expérience

```bash
cd ..
python src/main.py | tee experiments/run_$(date +%Y%m%d_%H%M%S).txt
```

Les résultats structurés sont sauvegardés automatiquement dans `results/results.csv`.
