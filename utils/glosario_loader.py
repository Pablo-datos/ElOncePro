import pandas as pd
import os

def load_glosario_tactico(path='data/glosario_tactico.csv'):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Glosario no encontrado en {path}")
    df = pd.read_csv(path)
    df = df.dropna(subset=['id_principio', 'principio'])
    df['principio_display'] = df.apply(lambda row: add_icon(row), axis=1)
    return df

def add_icon(row):
    cat = row.get("categoría", "").lower()
    if "ofensivo" in cat:
        icon = "⚔️"
    elif "defensivo" in cat:
        icon = "🛡️"
    elif "balón parado" in cat:
        icon = "🎯"
    else:
        icon = "📌"
    return f"{icon} {row['principio']}"
