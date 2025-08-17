# controllers/modelo_prediccion.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neighbors import NearestNeighbors
import joblib
import os
from datetime import datetime
import warnings
import logging

warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictorTactico:
    """
    Sistema de ML para predecir principios tácticos basado en historial
    Versión blindada con manejo exhaustivo de errores
    """
    
    def __init__(self, model_path="models/predictor_tactico.pkl"):
        self.model_path = model_path
        self.model = None
        self.encoders = {}
        self.mlb = MultiLabelBinarizer()
        self.feature_columns = ['categoria', 'bloque', 'dia', 'mes_temporada']
        self.is_trained = False
        self.min_samples_required = 10
        self.model_version = "2.0"  # Versión para detectar modelos incompatibles
        
        # Crear directorio si no existe
        try:
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"No se pudo crear directorio de modelos: {e}")
        
        # Cargar modelo si existe
        self.cargar_modelo()
    
    def validar_datos_entrada(self, df):
        """
        Valida que el DataFrame tenga la estructura esperada
        """
        if df is None or df.empty:
            return False, "No hay datos para procesar"
        
        # Verificar columnas requeridas
        columnas_requeridas = ['categoria', 'bloque', 'dia', 'principio']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            return False, f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}"
        
        # Verificar que no todas las filas estén vacías
        if df[columnas_requeridas].dropna(how='all').empty:
            return False, "Todos los registros están vacíos"
        
        # Verificar tipos de datos básicos
        for col in ['categoria', 'bloque', 'dia', 'principio']:
            if col in df.columns:
                # Convertir a string y limpiar
                df[col] = df[col].astype(str).str.strip()
                # Eliminar valores 'nan' o vacíos
                df = df[df[col] != 'nan']
                df = df[df[col] != '']
        
        if len(df) < self.min_samples_required:
            return False, f"Se necesitan al menos {self.min_samples_required} registros válidos. Actualmente: {len(df)}"
        
        return True, "Datos válidos"
    
    def preparar_features(self, df):
        """
        Prepara las características para el modelo con manejo robusto de errores
        """
        try:
            df_prep = df.copy()
            
            # Extraer mes de la temporada si existe
            if 'id_temporada' in df_prep.columns:
                try:
                    df_prep['mes_temporada'] = pd.to_datetime(
                        df_prep['id_temporada'].astype(str), 
                        format='%Y-%m',
                        errors='coerce'
                    ).dt.month.fillna(1)
                except:
                    df_prep['mes_temporada'] = 1
            else:
                df_prep['mes_temporada'] = 1
            
            # Codificar variables categóricas de forma segura
            for col in ['categoria', 'bloque', 'dia']:
                if col in df_prep.columns:
                    # Asegurar que son strings
                    df_prep[col] = df_prep[col].astype(str).str.strip()
                    
                    if col not in self.encoders:
                        self.encoders[col] = LabelEncoder()
                        try:
                            df_prep[f'{col}_encoded'] = self.encoders[col].fit_transform(df_prep[col])
                        except Exception as e:
                            logger.error(f"Error codificando {col}: {e}")
                            df_prep[f'{col}_encoded'] = 0
                    else:
                        # Manejar categorías no vistas de forma segura
                        df_prep[f'{col}_encoded'] = df_prep[col].apply(
                            lambda x: self._encode_safe(col, x)
                        )
            
            return df_prep
            
        except Exception as e:
            logger.error(f"Error preparando features: {e}")
            # Retornar DataFrame con columnas encoded en 0
            for col in ['categoria', 'bloque', 'dia']:
                df_prep[f'{col}_encoded'] = 0
            df_prep['mes_temporada'] = 1
            return df_prep
    
    def _encode_safe(self, encoder_name, value):
        """
        Codifica un valor de forma segura, manejando valores no vistos
        """
        try:
            if str(value) in self.encoders[encoder_name].classes_:
                return self.encoders[encoder_name].transform([str(value)])[0]
            else:
                # Valor no visto, retornar -1
                return -1
        except:
            return -1
    
    def entrenar_modelo(self, df, test_size=0.2):
        """
        Entrena el modelo con los datos históricos de forma robusta
        """
        try:
            # Validar datos de entrada
            es_valido, mensaje = self.validar_datos_entrada(df)
            if not es_valido:
                return False, mensaje
            
            # Limpiar datos
            df_limpio = df.dropna(subset=['categoria', 'bloque', 'dia', 'principio'])
            
            # Preparar datos
            df_prep = self.preparar_features(df_limpio)
            
            # Agrupar principios por día/bloque/categoría
            try:
                grouped = df_prep.groupby(
                    ['categoria', 'bloque', 'dia', 'mes_temporada']
                )['principio'].apply(list).reset_index()
            except Exception as e:
                return False, f"Error agrupando datos: {str(e)}"
            
            # Verificar combinaciones únicas
            if len(grouped) < self.min_samples_required:
                return False, f"Se necesitan al menos {self.min_samples_required} combinaciones únicas. Actualmente: {len(grouped)}"
            
            # Preparar features
            X = grouped[['categoria', 'bloque', 'dia', 'mes_temporada']]
            X = self.preparar_features(X)
            
            # Verificar que la preparación fue exitosa
            feature_cols = ['categoria_encoded', 'bloque_encoded', 'dia_encoded', 'mes_temporada']
            for col in feature_cols:
                if col not in X.columns:
                    return False, f"Error en preparación de datos: falta columna {col}"
            
            X_encoded = X[feature_cols]
            
            # Preparar target (multilabel)
            try:
                y = self.mlb.fit_transform(grouped['principio'])
            except Exception as e:
                return False, f"Error preparando etiquetas: {str(e)}"
            
            # Verificar que hay suficientes muestras para split
            if len(X_encoded) < 4:  # Mínimo para train_test_split
                return False, "No hay suficientes muestras para dividir en entrenamiento/prueba"
            
            # División train/test
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_encoded, y, test_size=test_size, random_state=42
                )
            except Exception as e:
                return False, f"Error dividiendo datos: {str(e)}"
            
            # Entrenar modelo
            base_model = RandomForestClassifier(
                n_estimators=50,  # Reducido para datasets pequeños
                max_depth=5,      # Limitado para evitar overfitting
                min_samples_split=2,
                random_state=42,
                n_jobs=-1
            )
            
            self.model = MultiOutputClassifier(base_model)
            
            try:
                self.model.fit(X_train, y_train)
            except Exception as e:
                return False, f"Error entrenando modelo: {str(e)}"
            
            # Evaluar
            try:
                y_pred = self.model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
            except:
                accuracy = 0.0
                f1 = 0.0
            
            self.is_trained = True
            
            # Guardar estadísticas
            self.stats = {
                'fecha_entrenamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_registros': len(df_limpio),
                'combinaciones_unicas': len(grouped),
                'accuracy': float(accuracy),
                'f1_score': float(f1),
                'categorias': list(df_limpio['categoria'].unique()),
                'bloques': list(df_limpio['bloque'].unique()),
                'dias': list(df_limpio['dia'].unique()),
                'total_principios': len(self.mlb.classes_),
                'version': self.model_version
            }
            
            # Guardar modelo
            exito_guardado = self.guardar_modelo()
            
            if not exito_guardado:
                return True, f"Modelo entrenado (Accuracy: {accuracy:.2f}) pero no se pudo guardar"
            
            return True, f"Modelo entrenado exitosamente. Accuracy: {accuracy:.2f}, F1: {f1:.2f}"
            
        except Exception as e:
            logger.error(f"Error general en entrenamiento: {e}")
            return False, f"Error inesperado al entrenar: {str(e)}"
    
    def predecir_principios(self, categoria, bloque, dia, temporada=None, n_sugerencias=5):
        """
        Predice los principios más probables con manejo robusto de errores
        """
        if not self.is_trained:
            return [], "El modelo no está entrenado. Por favor, entrena el modelo primero."
        
        try:
            # Validar inputs
            if not all([categoria, bloque, dia]):
                return [], "Debe proporcionar categoría, bloque y día"
            
            # Preparar entrada
            input_data = pd.DataFrame([{
                'categoria': str(categoria).strip(),
                'bloque': str(bloque).strip(),
                'dia': str(dia).strip(),
                'mes_temporada': 1 if temporada is None else self._extraer_mes(temporada)
            }])
            
            # Verificar si la combinación es conocida
            categoria_conocida = str(categoria).strip() in self.stats.get('categorias', [])
            bloque_conocido = str(bloque).strip() in self.stats.get('bloques', [])
            dia_conocido = str(dia).strip() in self.stats.get('dias', [])
            
            advertencias = []
            if not categoria_conocida:
                advertencias.append(f"Categoría '{categoria}' no vista en entrenamiento")
            if not bloque_conocido:
                advertencias.append(f"Bloque '{bloque}' no visto en entrenamiento")
            if not dia_conocido:
                advertencias.append(f"Día '{dia}' no visto en entrenamiento")
            
            # Preparar features
            input_prep = self.preparar_features(input_data)
            
            feature_cols = ['categoria_encoded', 'bloque_encoded', 'dia_encoded', 'mes_temporada']
            X = input_prep[feature_cols]
            
            # Verificar valores no vistos (-1)
            valores_no_vistos = (X.values[0] == -1).sum()
            
            if valores_no_vistos >= 2:  # Si hay 2 o más valores no vistos
                return [], "Combinación muy diferente a los datos de entrenamiento. No es posible hacer una predicción confiable."
            
            # Predecir
            try:
                if hasattr(self.model, 'predict_proba'):
                    # Obtener probabilidades para cada estimador
                    probas = []
                    for estimator in self.model.estimators_:
                        if hasattr(estimator, 'predict_proba'):
                            proba = estimator.predict_proba(X)[0]
                            # Manejar el caso donde solo hay una clase
                            if len(proba) == 1:
                                probas.append([1-proba[0], proba[0]])
                            else:
                                probas.append(proba)
                        else:
                            # Si no tiene predict_proba, usar predict
                            pred = estimator.predict(X)[0]
                            probas.append([1-pred, pred])
                else:
                    # Fallback a predicción binaria
                    preds = self.model.predict(X)
                    probas = [[1-p, p] for p in preds[0]]
                
            except Exception as e:
                logger.error(f"Error en predicción: {e}")
                return [], f"Error al realizar la predicción: {str(e)}"
            
            # Calcular scores para cada principio
            principios_scores = []
            for i, clase in enumerate(self.mlb.classes_):
                try:
                    if i < len(probas):
                        # Tomar la probabilidad de la clase positiva
                        prob = probas[i][1] if len(probas[i]) > 1 else 0.5
                    else:
                        prob = 0.0
                    principios_scores.append((clase, float(prob)))
                except:
                    principios_scores.append((clase, 0.0))
            
            # Ordenar por probabilidad
            principios_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Si hay advertencias, ajustar confianza
            factor_confianza = 1.0
            if advertencias:
                factor_confianza = 0.7 ** len(advertencias)  # Reducir confianza por cada valor no visto
            
            # Retornar top N
            sugerencias = []
            for p in principios_scores[:n_sugerencias]:
                if p[1] > 0.05:  # Umbral mínimo
                    confianza_ajustada = p[1] * factor_confianza
                    sugerencias.append({
                        'principio': p[0],
                        'confianza': confianza_ajustada,
                        'porcentaje': f"{confianza_ajustada*100:.1f}%",
                        'advertencias': advertencias if advertencias else None
                    })
            
            if not sugerencias:
                return [], "No se encontraron principios con suficiente confianza para esta combinación"
            
            return sugerencias, "Predicción exitosa" + (f" (con advertencias)" if advertencias else "")
            
        except Exception as e:
            logger.error(f"Error general en predicción: {e}")
            return [], f"Error inesperado: {str(e)}"
    
    def analizar_similitud_microciclos(self, df, microciclo_referencia, n_similares=3):
        """
        Encuentra microciclos similares con manejo robusto de errores
        """
        try:
            # Validar datos
            if df is None or df.empty:
                return [], "No hay datos para analizar"
            
            if 'nombre_microciclo' not in df.columns or 'principio' not in df.columns:
                return [], "Faltan columnas requeridas (nombre_microciclo, principio)"
            
            # Limpiar datos
            df_limpio = df.dropna(subset=['nombre_microciclo', 'principio'])
            
            # Agrupar por microciclo
            try:
                microciclo_principios = df_limpio.groupby('nombre_microciclo')['principio'].apply(list).to_dict()
            except Exception as e:
                return [], f"Error agrupando datos: {str(e)}"
            
            if not microciclo_principios:
                return [], "No se encontraron microciclos válidos"
            
            if microciclo_referencia not in microciclo_principios:
                microciclos_disponibles = list(microciclo_principios.keys())[:5]
                return [], f"Microciclo '{microciclo_referencia}' no encontrado. Disponibles: {', '.join(microciclos_disponibles)}..."
            
            # Solo analizar si hay más de un microciclo
            if len(microciclo_principios) <= 1:
                return [], "Se necesitan al menos 2 microciclos para comparar"
            
            # Vectorizar principios
            all_principios = set()
            for principios in microciclo_principios.values():
                if isinstance(principios, list):
                    all_principios.update(principios)
            
            if not all_principios:
                return [], "No se encontraron principios válidos"
            
            principios_list = sorted(list(all_principios))
            
            # Crear matriz de características
            vectores = []
            nombres = []
            
            for micro, principios in microciclo_principios.items():
                if isinstance(principios, list):
                    vector = [1 if p in principios else 0 for p in principios_list]
                    vectores.append(vector)
                    nombres.append(micro)
            
            if len(vectores) < 2:
                return [], "No hay suficientes datos para comparar"
            
            # Encontrar vecinos más cercanos
            X = np.array(vectores)
            n_neighbors = min(n_similares + 1, len(nombres))
            
            nbrs = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
            nbrs.fit(X)
            
            # Buscar índice del microciclo de referencia
            try:
                idx_ref = nombres.index(microciclo_referencia)
            except ValueError:
                return [], "Error al procesar microciclo de referencia"
            
            # Encontrar similares
            distances, indices = nbrs.kneighbors([X[idx_ref]])
            
            similares = []
            for i, (dist, idx) in enumerate(zip(distances[0][1:], indices[0][1:])):
                if idx < len(nombres):
                    similitud = max(0, 1 - dist)  # Asegurar que no sea negativo
                    similares.append({
                        'microciclo': nombres[idx],
                        'similitud': float(similitud),
                        'porcentaje': f"{similitud*100:.1f}%"
                    })
            
            return similares[:n_similares], "Análisis completado"
            
        except Exception as e:
            logger.error(f"Error en análisis de similitud: {e}")
            return [], f"Error al analizar similitud: {str(e)}"
    
    def predecir_carga_semanal(self, df, categoria):
        """
        Predice la carga semanal con manejo robusto
        """
        try:
            # Validar datos
            if df is None or df.empty:
                return None, "No hay datos para analizar"
            
            if 'categoria' not in df.columns:
                return None, "Falta la columna 'categoria'"
            
            # Filtrar por categoría
            df_cat = df[df['categoria'] == str(categoria).strip()]
            
            if df_cat.empty:
                categorias_disponibles = df['categoria'].unique()[:5]
                return None, f"No hay datos para categoría '{categoria}'. Disponibles: {', '.join(map(str, categorias_disponibles))}..."
            
            # Verificar columnas necesarias
            if 'nombre_microciclo' not in df_cat.columns or 'dia' not in df_cat.columns:
                return None, "Faltan columnas necesarias para el análisis"
            
            # Calcular estadísticas
            try:
                # Contar principios por día en cada microciclo
                stats_por_dia = df_cat.groupby(['nombre_microciclo', 'dia']).size().reset_index(name='count')
                
                # Estadísticas por microciclo
                stats_por_micro = stats_por_dia.groupby('nombre_microciclo')['count'].agg(['sum', 'mean', 'std'])
                
                if stats_por_micro.empty:
                    return None, "No hay suficientes datos para calcular estadísticas"
                
                # Calcular predicción
                carga_predicha = {
                    'total_principios_semana': float(stats_por_micro['sum'].mean()),
                    'promedio_por_dia': float(stats_por_micro['mean'].mean()),
                    'desviacion': float(stats_por_micro['std'].mean()) if len(stats_por_micro) > 1 else 0,
                    'dias_activos': df_cat['dia'].nunique(),
                    'microciclos_analizados': len(stats_por_micro),
                    'rango_sugerido': {
                        'min': int(stats_por_micro['sum'].min()) if len(stats_por_micro) > 0 else 0,
                        'max': int(stats_por_micro['sum'].max()) if len(stats_por_micro) > 0 else 0
                    }
                }
                
                return carga_predicha, "Cálculo exitoso"
                
            except Exception as e:
                return None, f"Error en cálculos estadísticos: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error en predicción de carga: {e}")
            return None, f"Error al calcular carga semanal: {str(e)}"
    
    def obtener_estadisticas_modelo(self):
        """
        Retorna estadísticas del modelo si está entrenado
        """
        if not self.is_trained:
            return {
                'estado': 'No entrenado',
                'mensaje': 'El modelo aún no ha sido entrenado'
            }
        
        return self.stats
    
    def guardar_modelo(self):
        """
        Guarda el modelo con manejo de errores
        """
        try:
            modelo_data = {
                'model': self.model,
                'encoders': self.encoders,
                'mlb': self.mlb,
                'stats': self.stats,
                'is_trained': self.is_trained,
                'version': self.model_version
            }
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Guardar con backup (blindado para Windows)
            if os.path.exists(self.model_path):
                backup_path = self.model_path + '.backup'
                if os.path.exists(backup_path):
                    os.remove(backup_path)  # evita WinError 183 si ya existe
                os.rename(self.model_path, backup_path)
            
            joblib.dump(modelo_data, self.model_path)
            return True
            
        except Exception as e:
            logger.error(f"Error guardando modelo: {e}")
            # Intentar restaurar backup
            backup_path = self.model_path + '.backup'
            if os.path.exists(backup_path):
                os.rename(backup_path, self.model_path)
            return False
    
    def cargar_modelo(self):
        """
        Carga modelo con manejo robusto de errores
        """
        if not os.path.exists(self.model_path):
            logger.info("No se encontró modelo previo")
            return False
        
        try:
            modelo_data = joblib.load(self.model_path)
            
            # Verificar versión
            version_guardada = modelo_data.get('version', '1.0')
            if version_guardada != self.model_version:
                logger.warning(f"Versión de modelo diferente ({version_guardada} vs {self.model_version})")
            
            # Cargar componentes
            self.model = modelo_data.get('model')
            self.encoders = modelo_data.get('encoders', {})
            self.mlb = modelo_data.get('mlb', MultiLabelBinarizer())
            self.stats = modelo_data.get('stats', {})
            self.is_trained = modelo_data.get('is_trained', False)
            
            # Validar que el modelo está completo
            if self.model is None or not self.encoders:
                logger.warning("Modelo incompleto, marcando como no entrenado")
                self.is_trained = False
                return False
            
            logger.info("Modelo cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            self.is_trained = False
            # Intentar eliminar modelo corrupto
            try:
                os.rename(self.model_path, self.model_path + '.corrupto')
            except:
                pass
            return False
    
    def resetear_modelo(self):
        """
        Resetea el modelo completamente
        """
        try:
            # Backup antes de resetear
            if os.path.exists(self.model_path):
                backup_path = self.model_path + f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                os.rename(self.model_path, backup_path)
            
            # Resetear estado
            self.model = None
            self.encoders = {}
            self.mlb = MultiLabelBinarizer()
            self.is_trained = False
            self.stats = {}
            
            return True, "Modelo reseteado correctamente"
            
        except Exception as e:
            return False, f"Error al resetear modelo: {str(e)}"
    
    def _extraer_mes(self, temporada):
        """
        Extrae el mes de una temporada de forma segura
        """
        try:
            return pd.to_datetime(str(temporada), format='%Y-%m', errors='coerce').month or 1
        except:
            return 1

# Funciones de conveniencia
predictor_global = None

def obtener_predictor():
    """Obtiene la instancia global del predictor"""
    global predictor_global
    if predictor_global is None:
        predictor_global = PredictorTactico()
    return predictor_global

def entrenar_modelo_global(df):
    """Entrena el modelo con datos actuales"""
    predictor = obtener_predictor()
    return predictor.entrenar_modelo(df)

def predecir_principios_global(categoria, bloque, dia, temporada=None, n_sugerencias=5):
    """Predice principios usando el modelo global"""
    predictor = obtener_predictor()
    return predictor.predecir_principios(categoria, bloque, dia, temporada, n_sugerencias)

def resetear_modelo_global():
    """Resetea el modelo global"""
    predictor = obtener_predictor()
    return predictor.resetear_modelo()
