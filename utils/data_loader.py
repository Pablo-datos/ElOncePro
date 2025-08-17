import pandas as pd
import os

# Rutas de los archivos CSV
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

MICROCICLOS_FILE = os.path.join(DATA_DIR, 'microciclos.csv')
TEMPORADAS_FILE = os.path.join(DATA_DIR, 'temporadas.csv')
GLOSARIO_FILE = os.path.join(DATA_DIR, 'glosario_tactico.csv')


def load_microciclos():
    try:
        df = pd.read_csv(MICROCICLOS_FILE)
        return df
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {MICROCICLOS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error al cargar microciclos: {e}")
        return pd.DataFrame()


def load_temporadas():
    try:
        df = pd.read_csv(TEMPORADAS_FILE)
        return df
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {TEMPORADAS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error al cargar temporadas: {e}")
        return pd.DataFrame()


def load_glosario_tactico():
    try:
        df = pd.read_csv(GLOSARIO_FILE)
        
        # Validamos la columna clave
        if 'nombre_principio' not in df.columns:
            raise KeyError("⚠️ La columna 'nombre_principio' no existe en glosario_tactico.csv")
        
        # Eliminamos duplicados si los hubiera
        df = df.drop_duplicates(subset=['nombre_principio']).reset_index(drop=True)
        return df
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {GLOSARIO_FILE}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Error al cargar glosario táctico: {e}")
        return pd.DataFrame()
