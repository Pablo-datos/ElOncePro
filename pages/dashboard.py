# pages/dashboard.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from controllers.proteccion import verificar_acceso, mostrar_info_usuario_sidebar, obtener_info_usuario, es_admin, es_entrenador
from controllers.planificador import cargar_datos_csv
from controllers.auth import listar_usuarios
from fpdf import FPDF
import io

# === Estilo global: fondo negro + texto blanco (El Once Pro) ===
st.markdown("""
<style>
  body, .stApp { background-color: #000000 !important; color: white !important; }
  .stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Verificar acceso - solo admin y entrenadores
verificar_acceso(roles_permitidos=["admin", "entrenador"])

# Configuración de página
st.set_page_config(
    page_title="Dashboard - Sistema de Planificación",
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
st.title("📊 Dashboard - Sistema de Planificación Táctica")
st.markdown(f"### Bienvenido, {info_usuario['nombre_completo']}")

# Mostrar fecha actual
st.caption(f"📅 {datetime.now().strftime('%d de %B de %Y')}")

st.markdown("---")

# =====================
# CARGAR DATOS
# =====================
try:
    # Cargar todos los archivos necesarios
    df_planif = pd.read_csv("data/planificacion_microciclos.csv") if os.path.exists("data/planificacion_microciclos.csv") else pd.DataFrame()
    df_temporadas = cargar_datos_csv("data/temporadas.csv")
    df_microciclos = cargar_datos_csv("data/microciclos.csv")
    df_categorias = cargar_datos_csv("data/categorias.csv")
    df_club = pd.read_csv("data/club_info.csv") if os.path.exists("data/club_info.csv") else pd.DataFrame()
    
    # Solo admin puede ver usuarios
    if es_admin():
        df_usuarios = listar_usuarios()
    
except Exception as e:
    st.error(f"Error al cargar datos: {str(e)}")
    df_planif = pd.DataFrame()

# =====================
# MÉTRICAS PRINCIPALES
# =====================
st.markdown("### 📈 Métricas Generales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_microciclos = len(df_microciclos) if not df_microciclos.empty else 0
    st.metric(
        "Microciclos Totales",
        total_microciclos,
        "↑ 2 nuevos" if total_microciclos > 0 else None
    )

with col2:
    categorias_activas = len(df_categorias) if not df_categorias.empty else 0
    st.metric(
        "Categorías Activas",
        categorias_activas
    )

with col3:
    if not df_planif.empty and 'principio' in df_planif.columns:
        principios_unicos = df_planif['principio'].nunique()
    else:
        principios_unicos = 0
    st.metric(
        "Principios Tácticos",
        principios_unicos
    )

with col4:
    if es_admin() and 'df_usuarios' in locals():
        usuarios_activos = len(df_usuarios[df_usuarios.get('activo', True)])
        st.metric(
            "Usuarios Activos",
            usuarios_activos
        )
    else:
        # Para entrenadores, mostrar solo su info
        st.metric(
            "Mi Rol",
            info_usuario['rol'].capitalize()
        )

st.markdown("---")

# =====================
# GRÁFICOS Y ANÁLISIS
# =====================
if not df_planif.empty:
    # Tabs para diferentes análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Análisis General",
        "📅 Actividad Temporal",
        "🎯 Principios Tácticos",
        "👥 Gestión" if es_admin() else "📋 Mis Datos"
    ])
    
    with tab1:
        st.subheader("📊 Análisis General del Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por categoría
            if 'categoria' in df_planif.columns:
                st.markdown("#### Planificaciones por Categoría")
                cat_counts = df_planif['categoria'].value_counts()
                
                fig1 = px.pie(
                    values=cat_counts.values,
                    names=cat_counts.index,
                    title="Distribución por Categoría",
                    hole=0.4
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Distribución por bloque
            if 'bloque' in df_planif.columns:
                st.markdown("#### Distribución por Tipo de Bloque")
                bloque_counts = df_planif['bloque'].value_counts()
                
                fig2 = px.bar(
                    x=bloque_counts.index,
                    y=bloque_counts.values,
                    title="Principios por Bloque",
                    labels={'x': 'Bloque', 'y': 'Cantidad'},
                    color=bloque_counts.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("📅 Análisis Temporal")
        
        # Si es entrenador, filtrar solo sus datos
        df_temporal = df_planif.copy()
        if es_entrenador() and not es_admin():
            # Aquí podrías filtrar por el entrenador actual si tienes esa información
            st.info("Mostrando datos de todas las categorías. En futuras versiones se filtrarán solo tus categorías asignadas.")
        
        # Actividad por día de la semana
        if 'dia' in df_temporal.columns:
            st.markdown("#### Actividad por Día de la Semana")
            
            dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            dia_counts = df_temporal['dia'].value_counts()
            
            # Reordenar según días de la semana
            dia_counts_ordenado = pd.Series(
                [dia_counts.get(dia, 0) for dia in dias_orden],
                index=dias_orden
            )
            
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=dia_counts_ordenado.index,
                y=dia_counts_ordenado.values,
                marker_color='lightblue',
                text=dia_counts_ordenado.values,
                textposition='auto',
            ))
            fig3.update_layout(
                title="Distribución de Actividades por Día",
                xaxis_title="Día de la Semana",
                yaxis_title="Cantidad de Principios"
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        # Timeline de microciclos
        if 'nombre_microciclo' in df_temporal.columns:
            st.markdown("#### Microciclos Más Activos")
            micro_counts = df_temporal['nombre_microciclo'].value_counts().head(10)
            
            fig4 = px.bar(
                x=micro_counts.values,
                y=micro_counts.index,
                orientation='h',
                title="Top 10 Microciclos con Más Principios",
                labels={'x': 'Cantidad', 'y': 'Microciclo'}
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab3:
        st.subheader("🎯 Análisis de Principios Tácticos")
        
        if 'principio' in df_planif.columns:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Top principios más utilizados
                st.markdown("#### Top 15 Principios Más Utilizados")
                principios_top = df_planif['principio'].value_counts().head(15)
                
                fig5 = px.treemap(
                    names=principios_top.index,
                    parents=[""] * len(principios_top),
                    values=principios_top.values,
                    title="Mapa de Principios Tácticos"
                )
                st.plotly_chart(fig5, use_container_width=True)
            
            with col2:
                # Estadísticas de principios
                st.markdown("#### Estadísticas")
                st.metric("Total Principios Únicos", df_planif['principio'].nunique())
                st.metric("Principio Más Usado", principios_top.index[0] if len(principios_top) > 0 else "N/A")
                st.metric("Frecuencia Máxima", principios_top.values[0] if len(principios_top) > 0 else 0)
                
                # Diversidad de principios
                total_registros = len(df_planif)
                principios_unicos = df_planif['principio'].nunique()
                diversidad = round((principios_unicos / total_registros * 100), 1) if total_registros > 0 else 0
                st.metric("Índice de Diversidad", f"{diversidad}%")
    
    with tab4:
        if es_admin():
            st.subheader("👥 Gestión del Sistema")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Usuarios del sistema
                st.markdown("#### Usuarios del Sistema")
                if 'df_usuarios' in locals() and not df_usuarios.empty:
                    # Contar por rol
                    rol_counts = df_usuarios['rol'].value_counts()
                    
                    fig6 = px.pie(
                        values=rol_counts.values,
                        names=rol_counts.index,
                        title="Distribución de Usuarios por Rol",
                        hole=0.3
                    )
                    st.plotly_chart(fig6, use_container_width=True)
                    
                    # Lista de usuarios
                    with st.expander("Ver lista de usuarios"):
                        st.dataframe(
                            df_usuarios[['usuario', 'nombre_completo', 'rol', 'activo']],
                            use_container_width=True,
                            hide_index=True
                        )
            
            with col2:
                # Estadísticas del sistema
                st.markdown("#### Estadísticas del Sistema")
                
                # Calcular estadísticas
                total_registros = len(df_planif)
                categorias_con_datos = df_planif['categoria'].nunique() if 'categoria' in df_planif.columns else 0
                microciclos_con_datos = df_planif['nombre_microciclo'].nunique() if 'nombre_microciclo' in df_planif.columns else 0
                
                # Mostrar métricas
                st.metric("Total Registros en BD", total_registros)
                st.metric("Categorías con Datos", categorias_con_datos)
                st.metric("Microciclos Planificados", microciclos_con_datos)
                
                # Botón para ir a gestión de usuarios
                st.markdown("---")
                if st.button("⚙️ Ir a Gestión de Usuarios", type="primary"):
                    st.switch_page("app.py")  # O la página que tengas para gestión
        
        else:  # Para entrenadores
            st.subheader("📋 Mis Datos")
            st.info("Vista personalizada en desarrollo. Próximamente podrás ver solo tus categorías asignadas.")
            
            # Mostrar info personal
            st.markdown("#### Mi Información")
            st.write(f"**Usuario:** {info_usuario['usuario']}")
            st.write(f"**Nombre:** {info_usuario['nombre_completo']}")
            st.write(f"**Rol:** {info_usuario['rol'].capitalize()}")
            st.write(f"**Email:** {info_usuario.get('email', 'No especificado')}")

    # =====================
    # EXPORTACIÓN DASHBOARD
    # =====================
    def generar_pdf_dashboard():
        """Helper para generar PDF del dashboard"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Dashboard - Sistema de Planificación Táctica", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d de %B de %Y')}", ln=True)
        pdf.cell(0, 10, f"Usuario: {info_usuario['nombre_completo']} ({info_usuario['rol']})", ln=True)
        pdf.ln(10)
        
        # Métricas principales
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Métricas Principales:", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 10, f"Microciclos Totales: {total_microciclos}", ln=True)
        pdf.cell(0, 10, f"Categorías Activas: {categorias_activas}", ln=True)
        pdf.cell(0, 10, f"Principios Tácticos: {principios_unicos}", ln=True)
        
        if not df_planif.empty:
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Estadísticas de Planificación:", ln=True)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 10, f"Total registros: {len(df_planif)}", ln=True)
            if 'categoria' in df_planif.columns:
                pdf.cell(0, 10, f"Categorías con datos: {df_planif['categoria'].nunique()}", ln=True)
            if 'nombre_microciclo' in df_planif.columns:
                pdf.cell(0, 10, f"Microciclos planificados: {df_planif['nombre_microciclo'].nunique()}", ln=True)
        
        return bytes(pdf.output(dest='S'))

    def generar_excel_dashboard():
        """Helper para generar Excel del dashboard"""
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            # Métricas principales
            metricas = pd.DataFrame([{
                "Fecha": datetime.now().strftime('%d de %B de %Y'),
                "Usuario": info_usuario['nombre_completo'],
                "Rol": info_usuario['rol'],
                "Microciclos_Totales": total_microciclos,
                "Categorias_Activas": categorias_activas,
                "Principios_Tacticos": principios_unicos
            }])
            metricas.to_excel(writer, index=False, sheet_name="Metricas")
            
            # Datos de planificación si existen
            if not df_planif.empty:
                df_planif.to_excel(writer, index=False, sheet_name="Planificacion")
            
            # Microciclos
            if not df_microciclos.empty:
                df_microciclos.to_excel(writer, index=False, sheet_name="Microciclos")
            
            # Temporadas
            if not df_temporadas.empty:
                df_temporadas.to_excel(writer, index=False, sheet_name="Temporadas")
        
        return buffer.getvalue()

    st.markdown("### 📤 Exportar Dashboard")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Exportar PDF", type="primary", use_container_width=True, key="export_pdf_btn_dash"):
            pdf_data = generar_pdf_dashboard()
            st.download_button(
                label="📥 Descargar PDF",
                data=pdf_data,
                file_name=f"dashboard_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime='application/pdf'
            )

    with col2:
        if st.button("📊 Exportar Excel", type="primary", use_container_width=True, key="export_xlsx_btn_dash"):
            excel_data = generar_excel_dashboard()
            st.download_button(
                label="📥 Descargar Excel",
                data=excel_data,
                file_name=f"dashboard_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.warning("No hay datos de planificación disponibles para mostrar en el dashboard.")
    st.info("Comienza creando microciclos y planificaciones en el módulo de Planificación.")

# =====================
# ACCIONES RÁPIDAS
# =====================
st.markdown("---")
st.markdown("### ⚡ Acciones Rápidas")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📋 Ir a Planificación", key="quick_planif_btn", use_container_width=True):
        st.switch_page("pages/planificacion.py")

with col2:
    if st.button("📊 Ver Planificaciones", key="quick_view_btn", use_container_width=True):
        st.switch_page("pages/vista_planificacion.py")

with col3:
    if es_admin():
        if st.button("👥 Gestionar Usuarios", key="quick_users_btn", use_container_width=True):
            st.switch_page("app.py")
    else:
        if st.button("🏠 Inicio", key="quick_home_btn", use_container_width=True):
            st.switch_page("app.py")

with col4:
    if st.button("🚪 Cerrar Sesión", key="quick_logout_btn", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

# Footer
st.markdown("---")
st.caption(f"Dashboard del Sistema de Planificación Táctica - {datetime.now().strftime('%Y')}")