# controllers/editor_microciclo.py

import streamlit as st
import pandas as pd
import os
from controllers.planificador import guardar_planificacion, cargar_datos_csv, normalize_for_matching

DATA_PATH = "data"
GLOSARIO_PATH = os.path.join(DATA_PATH, "glosario_tactico.csv")
PLANIFICACION_CSV = os.path.join(DATA_PATH, "planificacion_microciclos.csv")

def cargar_glosario():
    """Carga el glosario táctico desde CSV"""
    return pd.read_csv(GLOSARIO_PATH)

def cargar_planificacion_existente(id_temporada, categoria, microciclo):
    """
    Carga planificación existente con normalización robusta
    """
    if os.path.exists(PLANIFICACION_CSV):
        df = pd.read_csv(PLANIFICACION_CSV)
        df.columns = df.columns.str.strip().str.lower()
        
        # Usar normalización para matching robusto
        df_temp = df.copy()
        df_temp['id_temporada_norm'] = df_temp['id_temporada'].apply(normalize_for_matching)
        df_temp['categoria_norm'] = df_temp['categoria'].apply(normalize_for_matching)
        df_temp['nombre_microciclo_norm'] = df_temp['nombre_microciclo'].apply(normalize_for_matching)
        
        mask = (
            (df_temp['id_temporada_norm'] == normalize_for_matching(id_temporada)) &
            (df_temp['categoria_norm'] == normalize_for_matching(categoria)) &
            (df_temp['nombre_microciclo_norm'] == normalize_for_matching(microciclo))
        )
        
        return df[mask]
    return pd.DataFrame()

def mostrar_editor_microciclo(temporada, categoria, microciclo, glosario_df):
    """
    Editor principal del microciclo con guardado inteligente
    """
    st.subheader(f"📝 Editor del Microciclo – {microciclo}")
    
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    bloques = ["inicial", "situacional", "global", "global_competitiva", "final"]
    
    # Precargar datos existentes
    df_existente = cargar_planificacion_existente(temporada, categoria, microciclo)
    
    # Contenedor para tracking de cambios
    cambios_pendientes = []
    
    # Crear estructura de edición
    for dia in dias_semana:
        with st.expander(f"📅 {dia}"):
            for bloque in bloques:
                clave = f"{dia}_{bloque}"
                principios_guardados = []
                
                if not df_existente.empty:
                    # Buscar principios guardados con normalización
                    df_dia_bloque = df_existente[
                        (df_existente["dia"].apply(normalize_for_matching) == normalize_for_matching(dia)) &
                        (df_existente["bloque"].apply(normalize_for_matching) == normalize_for_matching(bloque))
                    ]
                    
                    if not df_dia_bloque.empty:
                        # Recolectar todos los principios individuales
                        principios_guardados = df_dia_bloque['principio'].dropna().tolist()
                
                # Formatear label del bloque
                label = f"**{bloque.replace('_', ' ').capitalize()}**"
                
                # Multiselect con estado inicial
                seleccionados = st.multiselect(
                    label,
                    glosario_df["principio"].unique(),
                    default=principios_guardados,
                    key=clave,
                    help=f"Selecciona principios tácticos para {bloque} del {dia}"
                )
                
                # Detectar cambios para mostrar indicador
                if set(seleccionados) != set(principios_guardados):
                    cambios_pendientes.append({
                        'dia': dia,
                        'bloque': bloque,
                        'antes': len(principios_guardados),
                        'despues': len(seleccionados)
                    })
    
    # Mostrar resumen de cambios si hay
    if cambios_pendientes:
        st.info(f"💡 Hay **{len(cambios_pendientes)}** bloques con cambios pendientes")
        
        # Opcional: mostrar detalle de cambios
        with st.expander("Ver detalle de cambios"):
            for cambio in cambios_pendientes:
                st.write(f"- **{cambio['dia']} - {cambio['bloque']}**: "
                        f"{cambio['antes']} → {cambio['despues']} principios")
    
    # Botón de guardado mejorado
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Botón habilitado solo si hay cambios o es primera vez
        hay_cambios = len(cambios_pendientes) > 0
        es_nuevo = df_existente.empty
        
        if st.button(
            "💾 **Guardar Planificación del Microciclo**", 
            type="primary", 
            use_container_width=True,
            disabled=not (hay_cambios or es_nuevo)
        ):
            # Progress bar para feedback visual
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            errores = []
            exitos = 0
            total_items = len(dias_semana) * len(bloques)
            current = 0
            
            # Guardar cada combinación día/bloque
            for dia in dias_semana:
                for bloque in bloques:
                    current += 1
                    progress_bar.progress(current / total_items)
                    status_text.text(f"Guardando {dia} - {bloque}...")
                    
                    seleccionados = st.session_state.get(f"{dia}_{bloque}", [])
                    
                    # Usar la función de guardado inteligente
                    # (que ya elimina duplicados automáticamente)
                    try:
                        success, mensaje = guardar_planificacion(
                            id_temporada=temporada,
                            categoria=categoria,
                            nombre_microciclo=microciclo,
                            dia=dia,
                            bloque=bloque,
                            principios=seleccionados
                        )
                        
                        if success:
                            exitos += 1
                        else:
                            errores.append(f"{dia}/{bloque}: {mensaje}")
                            
                    except Exception as e:
                        errores.append(f"{dia}/{bloque}: Error - {str(e)}")
            
            # Limpiar progress bar
            progress_bar.empty()
            status_text.empty()
            
            # Mostrar resultado final
            if errores:
                st.error(f"❌ Hubo {len(errores)} errores al guardar")
                with st.expander("Ver detalles de errores"):
                    for error in errores:
                        st.write(f"- {error}")
            else:
                st.success(f"✅ **Microciclo guardado correctamente**")
                st.write(f"Se actualizaron {exitos} bloques exitosamente")
                st.balloons()
                
                # Recargar para actualizar el estado
                import time
                time.sleep(1)
                st.rerun()
    
    # Información adicional
    with st.expander("ℹ️ Información sobre el editor"):
        st.markdown("""
        **Cómo usar el editor:**
        - Selecciona los principios tácticos para cada bloque de cada día
        - Los cambios se muestran en tiempo real
        - El sistema elimina duplicados automáticamente
        - Se crean backups antes de cada guardado
        - Puedes dejar bloques vacíos si no aplican
        
        **Bloques disponibles:**
        - **Inicial**: Calentamiento y activación
        - **Situacional**: Situaciones específicas de juego
        - **Global**: Trabajo integral del equipo
        - **Global Competitiva**: Simulación de competencia
        - **Final**: Vuelta a la calma y recuperación
        """)

# Función auxiliar para exportar configuración
def exportar_configuracion_microciclo(temporada, categoria, microciclo):
    """
    Exporta la configuración actual del microciclo a un diccionario
    """
    df_existente = cargar_planificacion_existente(temporada, categoria, microciclo)
    
    if df_existente.empty:
        return None
    
    configuracion = {}
    for _, row in df_existente.iterrows():
        dia = row['dia']
        bloque = row['bloque']
        principio = row['principio']
        
        if dia not in configuracion:
            configuracion[dia] = {}
        if bloque not in configuracion[dia]:
            configuracion[dia][bloque] = []
        
        configuracion[dia][bloque].append(principio)
    
    return configuracion