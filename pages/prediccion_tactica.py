# pages/prediccion_tactica.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from controllers.proteccion import verificar_acceso, mostrar_info_usuario_sidebar, es_admin, obtener_info_usuario
from controllers.modelo_prediccion import obtener_predictor, resetear_modelo_global
import os
from fpdf import FPDF
import io

# ✅ CONFIGURACIÓN DE PÁGINA PRIMERO (OBLIGATORIO EN STREAMLIT)
st.set_page_config(
    page_title="Predicción Táctica ML",
    page_icon="🤖",
    layout="wide"
)

# === Estilo global: fondo negro + texto blanco (El Once Pro) ===
st.markdown("""
<style>
  body, .stApp { background-color: #000000 !important; color: white !important; }
  .stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Verificar acceso
verificar_acceso(roles_permitidos=["admin", "entrenador"])

# Sidebar con info de usuario
mostrar_info_usuario_sidebar()

# Menú de navegación personalizado
if st.session_state.get("authenticated", False):
    st.markdown("<style>[data-testid='stSidebarNav']{display:none !important;}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 📁 Navegación")
        if st.button("📊 Dashboard", key="menu_dashboard_btn", use_container_width=True):
            st.switch_page("pages/dashboard.py")
        if st.button("📋 Planificación", key="menu_planificacion_btn", use_container_width=True):
            st.switch_page("pages/planificacion.py")
        if st.button("🤖 Predicción Táctica", key="menu_prediccion_btn", use_container_width=True):
            st.switch_page("pages/prediccion_tactica.py")
        if st.button("👁️ Vista Planificación", key="menu_vista_btn", use_container_width=True):
            st.switch_page("pages/vista_planificacion.py")
        st.markdown("---")

# Título principal
st.title("🤖 Predicción Táctica con Machine Learning")
st.markdown("Sistema inteligente de sugerencias basado en patrones históricos")

# =====================
# FUNCIONES AUXILIARES
# =====================
@st.cache_data
def cargar_datos_planificacion():
    """Carga y valida los datos de planificación"""
    try:
        # Verificar que el archivo existe
        archivo_path = "data/planificacion_microciclos.csv"
        
        if not os.path.exists(archivo_path):
            return pd.DataFrame(), "No existe archivo de planificación. Crea algunos microciclos primero."
        
        # Intentar cargar el archivo
        df = pd.read_csv(archivo_path)
        
        # Validación básica
        if df.empty:
            return pd.DataFrame(), "El archivo de planificación está vacío."
        
        # Verificar columnas mínimas
        columnas_requeridas = ['categoria', 'bloque', 'dia', 'principio']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            return pd.DataFrame(), f"Faltan columnas en el CSV: {', '.join(columnas_faltantes)}"
        
        # Limpiar datos básicos
        df = df.dropna(subset=columnas_requeridas, how='all')
        
        if len(df) == 0:
            return pd.DataFrame(), "No hay registros válidos en el archivo."
        
        return df, None
        
    except pd.errors.EmptyDataError:
        return pd.DataFrame(), "El archivo CSV está vacío o corrupto."
    except pd.errors.ParserError:
        return pd.DataFrame(), "Error al leer el archivo CSV. Verifica su formato."
    except Exception as e:
        return pd.DataFrame(), f"Error inesperado: {str(e)}"

def validar_datos_minimos(df):
    """Valida si hay suficientes datos para entrenar"""
    if df.empty:
        return False, "No hay datos disponibles"
    
    # Verificar combinaciones únicas
    if 'categoria' in df.columns and 'bloque' in df.columns and 'dia' in df.columns:
        combinaciones = df.groupby(['categoria', 'bloque', 'dia']).size()
        if len(combinaciones) < 10:
            return False, f"Solo hay {len(combinaciones)} combinaciones únicas. Se necesitan al menos 10."
    
    return True, "Datos suficientes"

# =====================
# CARGA DE DATOS
# =====================
df_planif, error = cargar_datos_planificacion()

# Obtener predictor
predictor = obtener_predictor()

# =====================
# MANEJO DE ERRORES INICIALES
# =====================
if error:
    st.error(f"⚠️ {error}")
    
    # Mostrar información de ayuda
    with st.expander("ℹ️ ¿Cómo solucionar este problema?"):
        st.markdown("""
        ### Pasos para comenzar:
        
        1. **Ve al módulo de Planificación** y crea al menos 2-3 microciclos completos
        2. **Asegúrate de guardar** los principios tácticos en diferentes días y bloques
        3. **Necesitas al menos 10 combinaciones** diferentes de categoría + bloque + día
        
        ### Estructura esperada del CSV:
        ```
        categoria,bloque,dia,principio,id_temporada,nombre_microciclo
        Juvenil A,inicial,Lunes,Presión alta,2024-01,Microciclo 1
        ...
        ```
        """)
    
    # Mostrar estado del modelo aunque no haya datos
    st.markdown("### 📊 Estado del Sistema")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.error("❌ Sin Datos")
        st.caption("No hay datos para procesar")
    
    with col2:
        if predictor.is_trained:
            st.warning("⚠️ Modelo Antiguo")
            st.caption("Modelo entrenado previamente")
        else:
            st.error("❌ Modelo No Entrenado")
            st.caption("Requiere datos para entrenar")
    
    with col3:
        st.info("ℹ️ Sistema Listo")
        st.caption("Esperando datos válidos")
    
    st.stop()

# =====================
# VALIDACIÓN DE DATOS MÍNIMOS
# =====================
datos_validos, mensaje_validacion = validar_datos_minimos(df_planif)

if not datos_validos:
    st.warning(f"⚠️ {mensaje_validacion}")
    st.info("💡 Continúa agregando más microciclos para mejorar las predicciones.")

# =====================
# FILA 1: ESTADO DEL MODELO Y ENTRENAMIENTO
# =====================
st.markdown("### 📊 Estado del Modelo")

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if predictor.is_trained:
        st.success("✅ Modelo Entrenado")
        stats = predictor.obtener_estadisticas_modelo()
        if isinstance(stats, dict) and 'accuracy' in stats:
            st.metric("Precisión", f"{stats['accuracy']*100:.1f}%")
        else:
            st.metric("Precisión", "N/A")
    else:
        st.warning("⚠️ Modelo No Entrenado")
        st.metric("Precisión", "N/A")

with col2:
    total_registros = len(df_planif) if not df_planif.empty else 0
    st.metric("Registros Históricos", f"{total_registros:,}")

with col3:
    if not df_planif.empty and 'categoria' in df_planif.columns:
        categorias_unicas = df_planif['categoria'].nunique()
    else:
        categorias_unicas = 0
    st.metric("Categorías", categorias_unicas)

with col4:
    if es_admin():
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # Botón de entrenamiento
            entrenar_disabled = not datos_validos
            if st.button("🔄 Entrenar", type="primary", disabled=entrenar_disabled, use_container_width=True, key="train_model_btn"):
                with st.spinner("Entrenando modelo..."):
                    exito, mensaje = predictor.entrenar_modelo(df_planif)
                    if exito:
                        st.success(mensaje)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(mensaje)
        
        with col_btn2:
            # Botón de reset (nuevo)
            if st.button("🗑️ Reset", type="secondary", disabled=not predictor.is_trained, use_container_width=True, key="reset_model_btn"):
                if st.checkbox("Confirmar reset del modelo", key="confirm_reset_chk"):
                    exito, mensaje = resetear_modelo_global()
                    if exito:
                        st.success(mensaje)
                        st.rerun()
                    else:
                        st.error(mensaje)
    else:
        st.info("Solo admin puede entrenar")
        if not datos_validos:
            st.caption("Datos insuficientes")

# Línea divisoria
st.markdown("---")

# =====================
# FILA 2: PREDICCIÓN DE PRINCIPIOS
# =====================
prediccion_habilitada = predictor.is_trained and not df_planif.empty

# Variable global para almacenar las últimas sugerencias
last_sugerencias = []

with st.expander("🎯 **Predicción de Principios Tácticos**", expanded=prediccion_habilitada):
    if not prediccion_habilitada:
        st.warning("⚠️ Debes entrenar el modelo primero con datos válidos.")
    else:
        st.markdown("Obtén sugerencias inteligentes para tu planificación")
        
        # Obtener valores únicos de forma segura
        try:
            categorias = sorted(df_planif['categoria'].dropna().unique()) if 'categoria' in df_planif.columns else []
            bloques = sorted(df_planif['bloque'].dropna().unique()) if 'bloque' in df_planif.columns else []
            dias = sorted(df_planif['dia'].dropna().unique()) if 'dia' in df_planif.columns else []
        except:
            categorias = []
            bloques = []
            dias = []
        
        if not all([categorias, bloques, dias]):
            st.error("No hay suficientes datos únicos para hacer predicciones")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                categoria_pred = st.selectbox("Categoría", categorias, key="cat_pred")
            
            with col2:
                bloque_pred = st.selectbox("Bloque", bloques, key="bloque_pred")
            
            with col3:
                dia_pred = st.selectbox("Día", dias, key="dia_pred")
            
            with col4:
                n_sugerencias = st.number_input("N° Sugerencias", min_value=3, max_value=10, value=5, key="n_sug_input")
            
            # Botón de predicción centrado
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔮 Generar Predicción", type="primary", use_container_width=True, key="gen_pred_btn"):
                    sugerencias, mensaje = predictor.predecir_principios(
                        categoria_pred, bloque_pred, dia_pred, n_sugerencias=n_sugerencias
                    )
                    
                    if sugerencias:
                        # Almacenar sugerencias para exportación
                        last_sugerencias = sugerencias
                        
                        # Verificar si hay advertencias
                        tiene_advertencias = any(s.get('advertencias') for s in sugerencias)
                        
                        if tiene_advertencias:
                            st.warning("⚠️ Predicción con advertencias - algunos valores no fueron vistos en entrenamiento")
                        else:
                            st.success("✅ Predicción generada exitosamente")
                        
                        # Mostrar resultados
                        st.markdown("#### 💡 Principios Sugeridos:")
                        
                        # Crear columnas dinámicas
                        cols = st.columns(min(3, len(sugerencias)))
                        
                        for i, sug in enumerate(sugerencias):
                            with cols[i % len(cols)]:
                                # Determinar color según confianza
                                confianza = sug.get('confianza', 0)
                                if confianza > 0.7:
                                    color = "🟢"
                                    delta_text = "Alta confianza"
                                elif confianza > 0.4:
                                    color = "🟡"
                                    delta_text = "Media confianza"
                                else:
                                    color = "🔴"
                                    delta_text = "Baja confianza"
                                
                                # Mostrar métrica
                                st.metric(
                                    label=f"{i+1}. {sug['principio'][:25]}{'...' if len(sug['principio']) > 25 else ''}",
                                    value=sug['porcentaje'],
                                    delta=f"{color} {delta_text}"
                                )
                                
                                # Mostrar principio completo
                                with st.container():
                                    st.caption(sug['principio'])
                                    
                                    # Mostrar advertencias si las hay
                                    if sug.get('advertencias'):
                                        for adv in sug['advertencias']:
                                            st.caption(f"⚠️ {adv}")
                        
                        # Gráfico de confianza
                        if len(sugerencias) > 0:
                            fig = go.Figure(go.Bar(
                                x=[s['principio'][:30] + "..." if len(s['principio']) > 30 else s['principio'] for s in sugerencias],
                                y=[s['confianza'] for s in sugerencias],
                                marker_color=['green' if s['confianza'] > 0.7 else 'yellow' if s['confianza'] > 0.4 else 'red' for s in sugerencias],
                                text=[s['porcentaje'] for s in sugerencias],
                                textposition='auto'
                            ))
                            fig.update_layout(
                                title="Nivel de Confianza por Principio",
                                xaxis_title="Principio",
                                yaxis_title="Confianza",
                                height=350,
                                xaxis_tickangle=-45
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                        # =====================
                        # EXPORTACIÓN SUGERENCIAS
                        # =====================
                        def generar_pdf_sugerencias():
                            """Helper para generar PDF de sugerencias"""
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", 'B', 16)
                            pdf.cell(0, 10, "Predicciones Tácticas ML", ln=True, align="C")
                            pdf.ln(10)
                            
                            info_usuario = obtener_info_usuario()
                            pdf.set_font("Arial", '', 12)
                            pdf.cell(0, 10, f"Categoría: {categoria_pred}", ln=True)
                            pdf.cell(0, 10, f"Bloque: {bloque_pred}", ln=True)
                            pdf.cell(0, 10, f"Día: {dia_pred}", ln=True)
                            pdf.cell(0, 10, f"N° Sugerencias: {n_sugerencias}", ln=True)
                            
                            pdf.ln(5)
                            pdf.set_font("Arial", 'I', 10)
                            pdf.cell(0, 10, f"Generado por: {info_usuario['nombre_completo']} ({info_usuario['rol']})", ln=True)
                            
                            # Sugerencias
                            pdf.ln(10)
                            pdf.set_font("Arial", 'B', 14)
                            pdf.cell(0, 10, "Principios Sugeridos:", ln=True)
                            
                            for i, sug in enumerate(last_sugerencias, 1):
                                pdf.ln(5)
                                pdf.set_font("Arial", 'B', 12)
                                pdf.cell(0, 10, f"{i}. {sug['principio']}", ln=True)
                                pdf.set_font("Arial", '', 11)
                                pdf.cell(0, 10, f"   Confianza: {sug['porcentaje']}", ln=True)
                                if sug.get('advertencias'):
                                    for adv in sug['advertencias']:
                                        pdf.cell(0, 10, f"   Advertencia: {adv}", ln=True)
                            
                            return bytes(pdf.output(dest='S'))

                        def generar_excel_sugerencias():
                            """Helper para generar Excel de sugerencias"""
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                                # Datos de sugerencias
                                df_sug = pd.DataFrame([{
                                    "Posicion": i+1,
                                    "Principio": sug['principio'],
                                    "Porcentaje": sug['porcentaje'],
                                    "Confianza": sug['confianza'],
                                    "Advertencias": ", ".join(sug.get('advertencias', []))
                                } for i, sug in enumerate(last_sugerencias)])
                                df_sug.to_excel(writer, index=False, sheet_name="Sugerencias")
                                
                                # Parámetros de predicción
                                params = pd.DataFrame([{
                                    "Categoria": categoria_pred,
                                    "Bloque": bloque_pred,
                                    "Dia": dia_pred,
                                    "N_Sugerencias": n_sugerencias,
                                    "Generado_por": obtener_info_usuario()['nombre_completo'],
                                    "Rol": obtener_info_usuario()['rol']
                                }])
                                params.to_excel(writer, index=False, sheet_name="Parametros")
                            
                            return buffer.getvalue()

                        st.markdown("### 📤 Exportar Sugerencias")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("📄 Exportar PDF", type="secondary", use_container_width=True, key="export_pdf_btn_pred_sug"):
                                pdf_data = generar_pdf_sugerencias()
                                st.download_button(
                                    label="📥 Descargar PDF",
                                    data=pdf_data,
                                    file_name=f"sugerencias_{categoria_pred}_{bloque_pred}_{dia_pred}.pdf",
                                    mime='application/pdf'
                                )

                        with col2:
                            if st.button("📊 Exportar Excel", type="secondary", use_container_width=True, key="export_xlsx_btn_pred_sug"):
                                excel_data = generar_excel_sugerencias()
                                st.download_button(
                                    label="📥 Descargar Excel",
                                    data=excel_data,
                                    file_name=f"sugerencias_{categoria_pred}_{bloque_pred}_{dia_pred}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                    else:
                        st.error(f"❌ {mensaje}")

# =====================
# FILA 3: ANÁLISIS AVANZADOS
# =====================
analisis_habilitado = not df_planif.empty

tab1, tab2, tab3 = st.tabs(["📈 Carga Semanal", "🔍 Similitud de Microciclos", "📊 Estadísticas del Modelo"])

with tab1:
    st.markdown("#### 📈 Predicción de Carga Semanal")
    
    if not analisis_habilitado:
        st.warning("⚠️ No hay datos disponibles para análisis")
    else:
        try:
            categorias = sorted(df_planif['categoria'].dropna().unique()) if 'categoria' in df_planif.columns else []
            
            if not categorias:
                st.error("No hay categorías disponibles")
            else:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    categoria_carga = st.selectbox("Selecciona Categoría", categorias, key="cat_carga")
                
                with col2:
                    if st.button("📊 Calcular Carga", type="primary", use_container_width=True, key="calc_carga_btn"):
                        carga, mensaje = predictor.predecir_carga_semanal(df_planif, categoria_carga)
                        
                        if carga:
                            # Métricas de carga
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric(
                                    "Principios/Semana",
                                    f"{carga['total_principios_semana']:.0f}",
                                    f"±{carga.get('desviacion', 0):.1f}"
                                )
                            
                            with col2:
                                st.metric(
                                    "Promedio/Día",
                                    f"{carga['promedio_por_dia']:.1f}"
                                )
                            
                            with col3:
                                st.metric(
                                    "Días Activos",
                                    carga.get('dias_activos', 0)
                                )
                            
                            with col4:
                                rango = carga.get('rango_sugerido', {})
                                st.metric(
                                    "Rango Sugerido",
                                    f"{rango.get('min', 0)}-{rango.get('max', 0)}"
                                )
                            
                            # Información adicional
                            st.info(f"📊 Análisis basado en {carga.get('microciclos_analizados', 0)} microciclos")
                            
                            # Visualización
                            try:
                                dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                                promedio_dia = carga.get('promedio_por_dia', 0)
                                dias_activos = carga.get('dias_activos', 5)
                                
                                valores_tipicos = [promedio_dia] * min(dias_activos, 7) + [0] * max(0, 7 - dias_activos)
                                
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=dias_semana,
                                    y=valores_tipicos[:7],
                                    name='Carga Típica',
                                    marker_color='lightblue',
                                    text=[f"{v:.1f}" if v > 0 else "" for v in valores_tipicos[:7]],
                                    textposition='auto'
                                ))
                                fig.update_layout(
                                    title=f"Distribución Semanal Típica - {categoria_carga}",
                                    xaxis_title="Día",
                                    yaxis_title="Principios Promedio",
                                    height=350
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error al generar gráfico: {str(e)}")
                        else:
                            st.error(f"❌ {mensaje}")
        except Exception as e:
            st.error(f"Error inesperado: {str(e)}")

with tab2:
    st.markdown("#### 🔍 Análisis de Similitud entre Microciclos")
    
    if not analisis_habilitado:
        st.warning("⚠️ No hay datos disponibles para análisis")
    else:
        try:
            microciclos_unicos = df_planif['nombre_microciclo'].dropna().unique() if 'nombre_microciclo' in df_planif.columns else []
            
            if len(microciclos_unicos) < 2:
                st.warning("Se necesitan al menos 2 microciclos diferentes para comparar")
            else:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    micro_ref = st.selectbox("Microciclo de Referencia", sorted(microciclos_unicos), key="micro_ref_sel")
                
                with col2:
                    max_similares = min(5, len(microciclos_unicos) - 1)
                    n_similares = st.number_input("N° Similares", min_value=1, max_value=max_similares, value=min(3, max_similares), key="n_sim_input")
                
                with col3:
                    if st.button("🔍 Buscar", type="primary", use_container_width=True, key="search_sim_btn"):
                        similares, mensaje = predictor.analizar_similitud_microciclos(
                            df_planif, micro_ref, n_similares
                        )
                        
                        if similares:
                            st.success("✅ Análisis completado")
                            
                            # Mostrar resultados
                            for i, sim in enumerate(similares, 1):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**{i}. {sim['microciclo']}**")
                                
                                with col2:
                                    similitud = sim.get('similitud', 0)
                                    if similitud > 0.8:
                                        emoji = "🟢"
                                    elif similitud > 0.6:
                                        emoji = "🟡"
                                    else:
                                        emoji = "🔴"
                                    st.write(f"{emoji} {sim['porcentaje']}")
                            
                            # Gráfico
                            if similares:
                                try:
                                    fig = px.bar(
                                        x=[s['microciclo'] for s in similares],
                                        y=[s['similitud'] for s in similares],
                                        title="Microciclos Más Similares",
                                        labels={'x': 'Microciclo', 'y': 'Similitud'},
                                        color=[s['similitud'] for s in similares],
                                        color_continuous_scale='RdYlGn',
                                        text=[s['porcentaje'] for s in similares]
                                    )
                                    fig.update_traces(textposition='auto')
                                    fig.update_layout(height=350)
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Error al generar gráfico: {str(e)}")
                        else:
                            st.error(f"❌ {mensaje}")
        except Exception as e:
            st.error(f"Error inesperado: {str(e)}")

with tab3:
    st.subheader("📊 Estadísticas del Modelo")
    
    if predictor.is_trained:
        stats = predictor.obtener_estadisticas_modelo()
        
        if isinstance(stats, dict) and 'accuracy' in stats:
            # Información del modelo en columnas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Métricas de Rendimiento:**")
                accuracy = stats.get('accuracy', 0)
                f1 = stats.get('f1_score', 0)
                st.write(f"- Precisión: {accuracy*100:.2f}%")
                st.write(f"- F1 Score: {f1*100:.2f}%")
                st.write(f"- Fecha de entrenamiento: {stats.get('fecha_entrenamiento', 'N/A')}")
                st.write(f"- Versión del modelo: {stats.get('version', 'N/A')}")
            
            with col2:
                st.markdown("**Datos de Entrenamiento:**")
                st.write(f"- Total registros: {stats.get('total_registros', 0):,}")
                st.write(f"- Combinaciones únicas: {stats.get('combinaciones_unicas', 0):,}")
                st.write(f"- Total principios: {stats.get('total_principios', 0)}")
                st.write(f"- Días únicos: {len(stats.get('dias', []))}")
            
            # =====================
            # EXPORTACIÓN ESTADÍSTICAS
            # =====================
            def generar_pdf_stats():
                """Helper para generar PDF de estadísticas"""
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Estadísticas del Modelo ML", ln=True, align="C")
                pdf.ln(10)
                
                info_usuario = obtener_info_usuario()
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Usuario: {info_usuario['nombre_completo']} ({info_usuario['rol']})", ln=True)
                pdf.ln(10)
                
                # Métricas de rendimiento
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Métricas de Rendimiento:", ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 10, f"Precisión: {accuracy*100:.2f}%", ln=True)
                pdf.cell(0, 10, f"F1 Score: {f1*100:.2f}%", ln=True)
                pdf.cell(0, 10, f"Fecha de entrenamiento: {stats.get('fecha_entrenamiento', 'N/A')}", ln=True)
                pdf.cell(0, 10, f"Versión del modelo: {stats.get('version', 'N/A')}", ln=True)
                
                # Datos de entrenamiento
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Datos de Entrenamiento:", ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 10, f"Total registros: {stats.get('total_registros', 0):,}", ln=True)
                pdf.cell(0, 10, f"Combinaciones únicas: {stats.get('combinaciones_unicas', 0):,}", ln=True)
                pdf.cell(0, 10, f"Total principios: {stats.get('total_principios', 0)}", ln=True)
                pdf.cell(0, 10, f"Días únicos: {len(stats.get('dias', []))}", ln=True)
                
                return bytes(pdf.output(dest='S'))

            def generar_excel_stats():
                """Helper para generar Excel de estadísticas"""
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    # Métricas principales
                    metricas = pd.DataFrame([{
                        "Precision": f"{accuracy*100:.2f}%",
                        "F1_Score": f"{f1*100:.2f}%",
                        "Fecha_Entrenamiento": stats.get('fecha_entrenamiento', 'N/A'),
                        "Version_Modelo": stats.get('version', 'N/A'),
                        "Total_Registros": stats.get('total_registros', 0),
                        "Combinaciones_Unicas": stats.get('combinaciones_unicas', 0),
                        "Total_Principios": stats.get('total_principios', 0),
                        "Dias_Unicos": len(stats.get('dias', [])),
                        "Generado_por": obtener_info_usuario()['nombre_completo'],
                        "Rol": obtener_info_usuario()['rol']
                    }])
                    metricas.to_excel(writer, index=False, sheet_name="Estadisticas")
                    
                    # Categorías, bloques y días
                    if stats.get('categorias'):
                        cat_df = pd.DataFrame(stats['categorias'], columns=["Categoria"])
                        cat_df.to_excel(writer, index=False, sheet_name="Categorias")
                    
                    if stats.get('bloques'):
                        bloques_df = pd.DataFrame(stats['bloques'], columns=["Bloque"])
                        bloques_df.to_excel(writer, index=False, sheet_name="Bloques")
                    
                    if stats.get('dias'):
                        dias_df = pd.DataFrame(stats['dias'], columns=["Dia"])
                        dias_df.to_excel(writer, index=False, sheet_name="Dias")
                
                return buffer.getvalue()

            st.markdown("### 📤 Exportar Estadísticas")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Exportar PDF", type="secondary", use_container_width=True, key="export_pdf_btn_pred_stats"):
                    pdf_data = generar_pdf_stats()
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_data,
                        file_name="estadisticas_modelo_ml.pdf",
                        mime='application/pdf'
                    )

            with col2:
                if st.button("📊 Exportar Excel", type="secondary", use_container_width=True, key="export_xlsx_btn_pred_stats"):
                    excel_data = generar_excel_stats()
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name="estadisticas_modelo_ml.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Distribución de datos
            with st.expander("Ver distribución de datos de entrenamiento"):
                # Categorías
                categorias_modelo = stats.get('categorias', [])
                if categorias_modelo:
                    st.markdown("**Categorías en el modelo:**")
                    st.write(", ".join(categorias_modelo))
                
                # Bloques
                bloques_modelo = stats.get('bloques', [])
                if bloques_modelo:
                    st.markdown("**Bloques en el modelo:**")
                    st.write(", ".join(bloques_modelo))
                
                # Días
                dias_modelo = stats.get('dias', [])
                if dias_modelo:
                    st.markdown("**Días en el modelo:**")
                    st.write(", ".join(dias_modelo))
                
                # Gráfico de distribución si hay datos
                if not df_planif.empty:
                    try:
                        df_dist = df_planif.groupby(['categoria', 'bloque']).size().reset_index(name='count')
                        if not df_dist.empty:
                            fig = px.treemap(
                                df_dist,
                                path=['categoria', 'bloque'],
                                values='count',
                                title='Distribución de Datos por Categoría y Bloque',
                                color='count',
                                color_continuous_scale='Blues'
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error al generar visualización: {str(e)}")
        else:
            st.error("El modelo está marcado como entrenado pero no tiene estadísticas válidas")
            if es_admin():
                st.info("💡 Intenta volver a entrenar el modelo")
    else:
        st.info("🔄 El modelo no está entrenado. Entrena el modelo para ver estadísticas detalladas.")
        
        # Mostrar información básica de los datos disponibles
        if not df_planif.empty:
            st.markdown("**Datos disponibles para entrenamiento:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Registros totales", len(df_planif))
            
            with col2:
                if 'categoria' in df_planif.columns:
                    st.metric("Categorías únicas", df_planif['categoria'].nunique())
            
            with col3:
                if all(col in df_planif.columns for col in ['categoria', 'bloque', 'dia']):
                    combinaciones = df_planif.groupby(['categoria', 'bloque', 'dia']).size()
                    st.metric("Combinaciones únicas", len(combinaciones))

# =====================
# FOOTER CON INFORMACIÓN
# =====================
st.markdown("---")

with st.expander("ℹ️ **Información sobre el Sistema de Predicción**"):
    st.markdown("""
    ### 🤖 ¿Cómo funciona?
    
    El sistema utiliza un modelo de **Random Forest Multi-Output** que aprende de los patrones históricos:
    
    1. **Entrada**: Categoría + Bloque + Día + Temporada
    2. **Procesamiento**: El modelo analiza combinaciones similares en el historial
    3. **Salida**: Top N principios más probables con nivel de confianza
    
    ### 📈 Métricas explicadas:
    
    - **Precisión**: % de predicciones correctas del modelo
    - **Confianza**: Probabilidad estimada para cada principio sugerido
    - **F1 Score**: Balance entre precisión y exhaustividad
    
    ### ⚠️ Limitaciones:
    
    - El modelo necesita al menos **10 combinaciones únicas** para entrenarse
    - Las predicciones son menos confiables para combinaciones no vistas en entrenamiento
    - La calidad mejora con más datos históricos
    
    ### 💡 Consejos:
    
    - Entrena el modelo regularmente con datos nuevos
    - Mayor historial = mejores predicciones
    - Las sugerencias son orientativas, usa tu criterio profesional
    - Si ves advertencias en las predicciones, significa que algunos valores no fueron vistos en el entrenamiento
    
    ### 🛠️ Solución de problemas:
    
    - **"No hay datos"**: Ve al módulo de Planificación y crea microciclos
    - **"Combinaciones insuficientes"**: Añade más variedad en días/bloques/categorías
    - **"Error al entrenar"**: Verifica que el CSV tenga las columnas correctas
    - **"Baja confianza"**: Normal para combinaciones nuevas, mejorará con más datos
    """)

# Información del usuario y estado final
info_usuario = obtener_info_usuario()
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.caption(f"Sistema de Predicción Táctica ML | Usuario: {info_usuario['nombre_completo']}")

with col2:
    if predictor.is_trained:
        st.caption("✅ Modelo operativo")
    else:
        st.caption("⚠️ Modelo no entrenado")

with col3:
    st.caption(f"📊 {len(df_planif) if not df_planif.empty else 0} registros")