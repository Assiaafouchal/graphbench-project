import pandas as pd
from conjecture import parse_conjecture_row


def load_benchmark(path):
    df = pd.read_excel(path)
    conjectures = []
    for _, row in df.iterrows():
        try:
            c = parse_conjecture_row(row)
            conjectures.append(c)
        except Exception as e:
            print(f"  [benchmark_loader] Ligne ignorée : {e}")
    print(f"  Benchmark chargé : {len(conjectures)} conjectures")
    return conjectures
