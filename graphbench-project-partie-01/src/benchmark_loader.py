import pandas as pd

def load_benchmark(path):

    df = pd.read_excel(path)

    print(df)

    return df