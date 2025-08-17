import pandas as pd
import os

def cargar_datos_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()

def cargar_glosario_tactico():
    return cargar_datos_csv("data/glosario_tactico.csv")

def obtener_microciclos_disponibles(df_microciclos, temporada_sel, categoria_sel):
    try:
        id_temporada = int(temporada_sel.split()[-1])
    except:
        id_temporada = df_microciclos["id_temporada"].iloc[0]  # fallback por seguridad
    return df_microciclos[
        (df_microciclos["categoria"] == categoria_sel) &
        (df_microciclos["id_temporada"] == id_temporada)
    ]

