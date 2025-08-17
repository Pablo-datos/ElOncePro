# controllers/planificador.py

import pandas as pd
import os

RUTA_CSV = "data/planificacion_microciclos.csv"

def guardar_planificacion(id_temporada, categoria, nombre_microciclo, dia, bloque, principios):
    """
    Guarda una entrada de planificación en el CSV.
    """
    nueva_fila = {
        "id_temporada": id_temporada,
        "categoria": categoria,
        "nombre_microciclo": nombre_microciclo,
        "dia": dia,
        "bloque": bloque,
        "principios": ', '.join(principios) if isinstance(principios, list) else principios
    }

    # Si el archivo ya existe, carga y agrega
    if os.path.exists(RUTA_CSV):
        df = pd.read_csv(RUTA_CSV)
        df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    else:
        df = pd.DataFrame([nueva_fila])

    df.to_csv(RUTA_CSV, index=False)


def cargar_planificacion(id_temporada, categoria, nombre_microciclo):
    """
    Carga las planificaciones existentes para un microciclo.
    """
    if os.path.exists(RUTA_CSV):
        df = pd.read_csv(RUTA_CSV)
        df_filtrado = df[
            (df["id_temporada"] == id_temporada) &
            (df["categoria"] == categoria) &
            (df["nombre_microciclo"] == nombre_microciclo)
        ]
        return df_filtrado
    else:
        return pd.DataFrame(columns=["id_temporada", "categoria", "nombre_microciclo", "dia", "bloque", "principios"])
