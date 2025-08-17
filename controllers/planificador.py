# controllers/planificador.py

import pandas as pd
import os
import shutil
from datetime import datetime
import unicodedata

RUTA_CSV = "data/planificacion_microciclos.csv"

def normalize_for_matching(text):
    """Función helper para normalizar texto y solucionar problemas de matching"""
    if pd.isna(text) or text is None:
        return ""
    
    text = str(text).strip()
    
    # Arregla el problema del float científico (2.024e+03 → 2024)
    try:
        if '.' in text and text.replace('.', '').replace('-', '').isdigit():
            float_val = float(text)
            if float_val.is_integer():
                text = str(int(float_val))
    except:
        pass
    
    # Normalización básica: quita acentos y lowercase
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower().strip()
    
    return text

def crear_backup(archivo_path):
    """Crea un backup del archivo antes de modificarlo"""
    if os.path.exists(archivo_path):
        backup_dir = "data/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(archivo_path)
        backup_path = os.path.join(backup_dir, f"{filename}_{timestamp}.bak")
        
        shutil.copy2(archivo_path, backup_path)
        return backup_path
    return None

def guardar_planificacion(id_temporada, categoria, nombre_microciclo, dia, bloque, principios):
    """
    Guarda una entrada de planificación en el CSV.
    Versión mejorada que elimina duplicados automáticamente.
    """
    return guardar_planificacion_inteligente(id_temporada, categoria, nombre_microciclo, dia, bloque, principios)

def guardar_planificacion_inteligente(id_temporada, categoria, nombre_microciclo, dia, bloque, principios):
    """
    Guarda la planificación de forma inteligente:
    - Elimina duplicados automáticamente
    - Maneja principios individualmente
    - Crea backups antes de modificar
    - Mantiene consistencia de datos
    """
    try:
        # Crear backup antes de modificar
        backup_path = crear_backup(RUTA_CSV)
        
        # Cargar datos existentes o crear DataFrame vacío
        if os.path.exists(RUTA_CSV):
            df = pd.read_csv(RUTA_CSV)
            # Limpiar columnas
            df.columns = df.columns.str.strip().str.lower()
        else:
            df = pd.DataFrame(columns=['id_temporada', 'categoria', 'nombre_microciclo', 
                                     'dia', 'bloque', 'principio', 'principios'])
        
        # Normalizar valores para matching
        id_temp_norm = normalize_for_matching(id_temporada)
        cat_norm = normalize_for_matching(categoria)
        micro_norm = normalize_for_matching(nombre_microciclo)
        dia_norm = normalize_for_matching(dia)
        bloque_norm = normalize_for_matching(bloque)
        
        # Crear copia temporal con columnas normalizadas
        df_temp = df.copy()
        for col in ['id_temporada', 'categoria', 'nombre_microciclo', 'dia', 'bloque']:
            if col in df.columns:
                df_temp[f'{col}_norm'] = df_temp[col].apply(normalize_for_matching)
        
        # Eliminar registros existentes para este día/bloque
        mask_eliminar = (
            (df_temp['id_temporada_norm'] == id_temp_norm) &
            (df_temp['categoria_norm'] == cat_norm) &
            (df_temp['nombre_microciclo_norm'] == micro_norm) &
            (df_temp['dia_norm'] == dia_norm) &
            (df_temp['bloque_norm'] == bloque_norm)
        )
        
        indices_eliminar = df_temp[mask_eliminar].index
        df_limpio = df.drop(indices_eliminar)
        
        # Crear nuevos registros (uno por principio)
        nuevos_registros = []
        principios_lista = principios if isinstance(principios, list) else [principios]
        
        for principio in principios_lista:
            if principio and principio.strip():  # Ignorar principios vacíos
                nuevo_registro = {
                    'id_temporada': id_temporada,
                    'categoria': categoria,
                    'nombre_microciclo': nombre_microciclo,
                    'dia': dia,
                    'bloque': bloque,
                    'principio': principio.strip(),
                    'principios': principio.strip()  # Mantener compatibilidad
                }
                nuevos_registros.append(nuevo_registro)
        
        # Concatenar con datos limpios
        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)
            df_final = pd.concat([df_limpio, df_nuevos], ignore_index=True)
        else:
            df_final = df_limpio
        
        # Guardar
        df_final.to_csv(RUTA_CSV, index=False)
        
        return True, f"Guardado: {len(nuevos_registros)} principios para {dia}/{bloque}"
        
    except Exception as e:
        # Restaurar backup si hay error
        if 'backup_path' in locals() and backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, RUTA_CSV)
        return False, f"Error al guardar: {str(e)}"

def cargar_datos_csv(ruta):
    """
    Carga datos desde un archivo CSV.
    """
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return pd.DataFrame()

def cargar_planificacion(id_temporada, categoria, nombre_microciclo):
    """
    Carga las planificaciones existentes para un microciclo.
    Versión mejorada con normalización robusta.
    """
    if os.path.exists(RUTA_CSV):
        df = pd.read_csv(RUTA_CSV)
        df.columns = df.columns.str.strip().str.lower()
        
        # Usar normalización para matching robusto
        df_temp = df.copy()
        df_temp['id_temporada_norm'] = df_temp['id_temporada'].apply(normalize_for_matching)
        df_temp['categoria_norm'] = df_temp['categoria'].apply(normalize_for_matching)
        df_temp['nombre_microciclo_norm'] = df_temp['nombre_microciclo'].apply(normalize_for_matching)
        
        mask = (
            (df_temp['id_temporada_norm'] == normalize_for_matching(id_temporada)) &
            (df_temp['categoria_norm'] == normalize_for_matching(categoria)) &
            (df_temp['nombre_microciclo_norm'] == normalize_for_matching(nombre_microciclo))
        )
        
        return df[mask]
    else:
        return pd.DataFrame(columns=["id_temporada", "categoria", "nombre_microciclo", 
                                   "dia", "bloque", "principio", "principios"])

def limpiar_y_migrar_datos():
    """
    Limpia y migra datos existentes:
    - Elimina duplicados
    - Separa principios concatenados
    - Normaliza estructura
    """
    if not os.path.exists(RUTA_CSV):
        return False, "No hay datos para migrar"
    
    try:
        # Backup antes de migrar
        backup_path = crear_backup(RUTA_CSV)
        
        # Cargar datos
        df = pd.read_csv(RUTA_CSV)
        df.columns = df.columns.str.strip().str.lower()
        
        # Verificar si necesita migración
        if 'principios' not in df.columns and 'principio' not in df.columns:
            return False, "Estructura de datos no reconocida"
        
        # Crear lista para datos migrados
        registros_migrados = []
        
        for _, row in df.iterrows():
            # Obtener principios (puede estar en 'principios' o 'principio')
            principios_str = row.get('principios', row.get('principio', ''))
            
            if pd.notna(principios_str) and str(principios_str).strip():
                # Si tiene comas, es un campo concatenado
                if ',' in str(principios_str):
                    principios_lista = [p.strip() for p in str(principios_str).split(',') if p.strip()]
                else:
                    principios_lista = [str(principios_str).strip()]
                
                # Crear un registro por cada principio
                for principio in principios_lista:
                    nuevo_registro = {
                        'id_temporada': row.get('id_temporada', ''),
                        'categoria': row.get('categoria', ''),
                        'nombre_microciclo': row.get('nombre_microciclo', ''),
                        'dia': row.get('dia', ''),
                        'bloque': row.get('bloque', ''),
                        'principio': principio,
                        'principios': principio  # Mantener compatibilidad
                    }
                    registros_migrados.append(nuevo_registro)
        
        # Crear DataFrame limpio
        df_migrado = pd.DataFrame(registros_migrados)
        
        # Eliminar duplicados exactos
        df_migrado = df_migrado.drop_duplicates()
        
        # Guardar
        df_migrado.to_csv(RUTA_CSV, index=False)
        
        return True, f"Migración completada: {len(df)} registros originales → {len(df_migrado)} registros limpios"
        
    except Exception as e:
        # Restaurar backup si hay error
        if 'backup_path' in locals() and backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, RUTA_CSV)
        return False, f"Error en migración: {str(e)}"