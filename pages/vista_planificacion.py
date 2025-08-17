# pages/vista_planificacion.py

import streamlit as st
import pandas as pd
import os
from controllers.proteccion import verificar_acceso, mostrar_info_usuario_sidebar, obtener_info_usuario, es_visor
from controllers.planificador import cargar_datos_csv
import plotly.express as px
from fpdf import FPDF
import io

# === Estilo global: fondo negro + texto blanco (El Once Pro) ===
st.markdown("""
<style>
  body, .stApp { background-color: #000000 !important; color: white !important; }
  .stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Verificar acceso - permitir visores, entrenadores y admin
verificar_acceso(roles_permitidos=["visor", "entrenador", "admin"])

# Configuración de página
st.set_page_config(
    page_title="Vista de Planificaciones",
    page_icon="📊",
    layout="wide"
)

# Mostrar información del usuario en sidebar
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

# Obtener información del usuario
info_usuario = obtener_info_usuario()

# =====================
# TÍTULO Y DESCRIPCIÓN
# =====================
st.title("📊 Vista de Planificaciones")
st.markdown(f"### Bienvenido, {info_usuario['nombre_completo']}")

if es_visor():
    st.info("👁️ Estás en modo de solo lectura. Puedes visualizar las planificaciones pero no editarlas ni exportarlas.")
else:
    st.info("📋 Puedes visualizar todas las planificaciones. Para editar, ve al módulo de Planificación.")

st.markdown("---")

# =====================
# CARGAR DATOS
# =====================
try:
    # Cargar archivo de planificación
    planif_csv = "data/planificacion_microciclos.csv"
    if not os.path.exists(planif_csv):
        st.warning("⚠️ No hay planificaciones guardadas aún.")
        st.stop()
    
    df_planif = pd.read_csv(planif_csv)
    
    if df_planif.empty:
        st.warning("⚠️ No hay datos de planificación disponibles.")
        st.stop()
    
    # Limpiar columnas
    df_planif.columns = df_planif.columns.str.strip().str.lower()
    
    # Cargar otros datos necesarios
    df_temporadas = cargar_datos_csv("data/temporadas.csv")
    df_microciclos = cargar_datos_csv("data/microciclos.csv")
    
except Exception as e:
    st.error(f"❌ Error al cargar datos: {str(e)}")
    st.stop()

# =====================
# FILTROS DE BÚSQUEDA
# =====================
st.sidebar.markdown("### 🔍 Filtros de Búsqueda")

# Filtro por temporada
temporadas_disponibles = df_planif['id_temporada'].unique() if 'id_temporada' in df_planif.columns else []
temporada_filtro = st.sidebar.selectbox(
    "Temporada",
    options=["Todas"] + list(temporadas_disponibles),
    key="filter_temp"
)

# Filtro por categoría
categorias_disponibles = df_planif['categoria'].unique() if 'categoria' in df_planif.columns else []
categoria_filtro = st.sidebar.selectbox(
    "Categoría",
    options=["Todas"] + list(categorias_disponibles),
    key="filter_cat"
)

# Filtro por microciclo
microciclos_disponibles = df_planif['nombre_microciclo'].unique() if 'nombre_microciclo' in df_planif.columns else []
microciclo_filtro = st.sidebar.selectbox(
    "Microciclo",
    options=["Todos"] + list(microciclos_disponibles),
    key="filter_micro"
)

# Aplicar filtros
df_filtrado = df_planif.copy()

if temporada_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado['id_temporada'] == temporada_filtro]

if categoria_filtro != "Todas":
    df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_filtro]

if microciclo_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado['nombre_microciclo'] == microciclo_filtro]

# =====================
# VISTA DE DATOS
# =====================
if df_filtrado.empty:
    st.warning("No se encontraron planificaciones con los filtros seleccionados.")
else:
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Registros", len(df_filtrado))
    
    with col2:
        dias_unicos = df_filtrado['dia'].nunique() if 'dia' in df_filtrado.columns else 0
        st.metric("📅 Días Planificados", dias_unicos)
    
    with col3:
        bloques_unicos = df_filtrado['bloque'].nunique() if 'bloque' in df_filtrado.columns else 0
        st.metric("📦 Bloques Únicos", bloques_unicos)
    
    with col4:
        principios_unicos = df_filtrado['principio'].nunique() if 'principio' in df_filtrado.columns else 0
        st.metric("🎯 Principios Únicos", principios_unicos)
    
    st.markdown("---")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📋 Tabla de Datos", "📊 Análisis Visual", "📈 Estadísticas"])
    
    with tab1:
        st.subheader("📋 Planificaciones Detalladas")
        
        # Preparar datos para mostrar
        columnas_mostrar = ['categoria', 'nombre_microciclo', 'dia', 'bloque', 'principio']
        columnas_disponibles = [col for col in columnas_mostrar if col in df_filtrado.columns]
        
        # Mostrar tabla
        st.dataframe(
            df_filtrado[columnas_disponibles],
            use_container_width=True,
            hide_index=True,
            column_config={
                "categoria": "Categoría",
                "nombre_microciclo": "Microciclo",
                "dia": "Día",
                "bloque": "Bloque",
                "principio": "Principio Táctico"
            }
        )
        
        # Exportación para NO visores
        if not es_visor():
            # =====================
            # EXPORTACIÓN VISTA PLANIFICACIÓN
            # =====================
            def generar_pdf_vista():
                """Helper para generar PDF de vista planificación"""
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Vista de Planificaciones", ln=True, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Total registros: {len(df_filtrado)}", ln=True)
                pdf.cell(0, 10, f"Temporada: {temporada_filtro}", ln=True)
                pdf.cell(0, 10, f"Categoría: {categoria_filtro}", ln=True)
                pdf.cell(0, 10, f"Microciclo: {microciclo_filtro}", ln=True)
                
                pdf.ln(5)
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 10, f"Generado por: {info_usuario['nombre_completo']} ({info_usuario['rol']})", ln=True)
                
                # Tabla resumen
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Resumen de Datos:", ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 10, f"Días únicos: {dias_unicos}", ln=True)
                pdf.cell(0, 10, f"Bloques únicos: {bloques_unicos}", ln=True)
                pdf.cell(0, 10, f"Principios únicos: {principios_unicos}", ln=True)
                
                return bytes(pdf.output(dest='S'))

            def generar_excel_vista():
                """Helper para generar Excel de vista planificación"""
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    # Datos filtrados
                    df_filtrado[columnas_disponibles].to_excel(writer, index=False, sheet_name="Planificaciones")
                    
                    # Resumen
                    resumen = pd.DataFrame([{
                        "Total_Registros": len(df_filtrado),
                        "Temporada_Filtro": temporada_filtro,
                        "Categoria_Filtro": categoria_filtro,
                        "Microciclo_Filtro": microciclo_filtro,
                        "Dias_Unicos": dias_unicos,
                        "Bloques_Unicos": bloques_unicos,
                        "Principios_Unicos": principios_unicos,
                        "Generado_por": info_usuario['nombre_completo'],
                        "Rol": info_usuario['rol']
                    }])
                    resumen.to_excel(writer, index=False, sheet_name="Resumen")
                
                return buffer.getvalue()

            st.markdown("### 📤 Exportar Vista")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Exportar PDF", type="primary", use_container_width=True, key="export_pdf_btn_vista"):
                    pdf_data = generar_pdf_vista()
                    st.download_button(
                        label="📥 Descargar PDF",
                        data=pdf_data,
                        file_name=f"vista_planificaciones_{categoria_filtro}_{microciclo_filtro}.pdf",
                        mime='application/pdf'
                    )

            with col2:
                if st.button("📊 Exportar Excel", type="primary", use_container_width=True, key="export_xlsx_btn_vista"):
                    excel_data = generar_excel_vista()
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_data,
                        file_name=f"vista_planificaciones_{categoria_filtro}_{microciclo_filtro}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.info("💡 Para exportar datos, usa el módulo de Planificación con los permisos adecuados.")
    
    with tab2:
        st.subheader("📊 Análisis Visual")
        
        # Gráfico 1: Distribución de principios por bloque
        if 'bloque' in df_filtrado.columns and 'principio' in df_filtrado.columns:
            st.markdown("#### Distribución de Principios por Bloque")
            
            df_bloques = df_filtrado.groupby('bloque').size().reset_index(name='cantidad')
            
            fig1 = px.bar(
                df_bloques,
                x='bloque',
                y='cantidad',
                title='Cantidad de Principios por Bloque',
                color='cantidad',
                color_continuous_scale='Blues'
            )
            fig1.update_layout(xaxis_title="Bloque", yaxis_title="Cantidad")
            st.plotly_chart(fig1, use_container_width=True)
        
        # Gráfico 2: Principios más utilizados
        if 'principio' in df_filtrado.columns:
            st.markdown("#### Top 10 Principios Más Utilizados")
            
            principios_count = df_filtrado['principio'].value_counts().head(10).reset_index()
            principios_count.columns = ['principio', 'frecuencia']
            
            fig2 = px.bar(
                principios_count,
                x='frecuencia',
                y='principio',
                orientation='h',
                title='Principios Tácticos Más Frecuentes',
                color='frecuencia',
                color_continuous_scale='Viridis'
            )
            fig2.update_layout(xaxis_title="Frecuencia", yaxis_title="Principio")
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.subheader("📈 Estadísticas Detalladas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Estadísticas por día
            if 'dia' in df_filtrado.columns:
                st.markdown("#### 📅 Distribución por Día")
                dias_stats = df_filtrado['dia'].value_counts()
                st.bar_chart(dias_stats)
        
        with col2:
            # Estadísticas por categoría
            if 'categoria' in df_filtrado.columns:
                st.markdown("#### 🏷️ Distribución por Categoría")
                cat_stats = df_filtrado['categoria'].value_counts()
                st.bar_chart(cat_stats)
        
        # Tabla resumen
        st.markdown("#### 📊 Resumen por Microciclo")
        if 'nombre_microciclo' in df_filtrado.columns:
            resumen = df_filtrado.groupby('nombre_microciclo').agg({
                'principio': 'count',
                'dia': 'nunique',
                'bloque': 'nunique'
            }).rename(columns={
                'principio': 'Total Principios',
                'dia': 'Días Únicos',
                'bloque': 'Bloques Únicos'
            })
            
            st.dataframe(resumen, use_container_width=True)

# =====================
# INFORMACIÓN ADICIONAL
# =====================
st.markdown("---")

with st.expander("ℹ️ Información sobre esta vista"):
    if es_visor():
        st.markdown("""
        **Como usuario con rol de Visor:**
        - ✅ Puedes ver todas las planificaciones
        - ✅ Puedes filtrar y analizar datos
        - ✅ Puedes ver gráficos y estadísticas
        - ❌ NO puedes editar planificaciones
        - ❌ NO puedes exportar datos
        - ❌ NO puedes eliminar registros
        
        Si necesitas realizar cambios o exportar datos, contacta con un administrador o entrenador.
        """)
    else:
        st.markdown("""
        **Opciones disponibles según tu rol:**
        - ✅ Ver todas las planificaciones
        - ✅ Filtrar y analizar datos
        - ✅ Para editar o exportar, usa el módulo de Planificación
        """)

# Footer
st.markdown("---")
st.caption("Sistema de Planificación Táctica - Vista de Solo Lectura")