import pandas as pd

# Cargar categorías
def load_categorias():
    return pd.read_csv("data/categorias.csv")

# Cargar temporadas
def load_temporadas():
    return pd.read_csv("data/temporadas.csv")

# Cargar microciclos
def load_microciclos():
    return pd.read_csv("data/microciclos.csv")
