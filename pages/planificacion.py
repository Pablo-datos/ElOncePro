import streamlit as st
import pandas as pd
from controllers.planificador import cargar_datos_csv
from controllers.editor_microciclo import mostrar_editor_microciclo
from controllers.resumen_microciclo import mostrar_resumen_microciclo
from controllers.editor_avanzado import mostrar_editor_avanzado
from controllers.proteccion import verificar_acceso, mostrar_info_usuario_sidebar, es_admin, obtener_info_usuario
import datetime
import os
import unicodedata
import re
from fpdf import FPDF
import io

# === Estilo global: fondo negro + texto blanco (El Once Pro) ===
st.markdown("""
<style>
  body, .stApp { background-color: #000000 !important; color: white !important; }
  .stButton > button { width: 100%; }
</style>
""", unsafe_allow_html=True)

# Verificar acceso - ahora "staff" no existe, usar "entrenador"
verificar_acceso(roles_permitidos=["admin", "entrenador"])

st.set_page_config(layout="wide", page_title="Planificación Táctica", page_icon="⚽")

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

# =====================
# FUNCIÓN HELPER PARA NORMALIZACIÓN ROBUSTA
# =====================
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

# =====================
# TÍTULO PRINCIPAL
# =====================
info_usuario = obtener_info_usuario()
st.title("📂 Planificación Táctica – Gestión de Microciclos")
st.markdown(f"**Usuario activo:** {info_usuario['nombre_completo']} ({info_usuario['rol']})")

# =====================
# CARGA DE DATOS INICIALES
# =====================
df_microciclos = cargar_datos_csv("data/microciclos.csv")
df_temporadas = cargar_datos_csv("data/temporadas.csv")

if df_temporadas.empty or df_microciclos.empty:
    st.error("❌ Error al cargar los datos. Verifica los archivos CSV.")
    st.stop()

# Cargar datos existentes
club_csv = "data/club_info.csv"
if not os.path.exists(club_csv):
    pd.DataFrame(columns=["nombre_club"]).to_csv(club_csv, index=False)

df_club = pd.read_csv(club_csv)
nombre_club = df_club["nombre_club"].values[0] if not df_club.empty else "F.C. Ejemplo Juvenil"

staff_csv = "data/staff_por_categoria.csv"
if not os.path.exists(staff_csv):
    pd.DataFrame(columns=["categoria", "entrenador", "staff", "fecha"]).to_csv(staff_csv, index=False)

# =====================
# FILA 1: CONFIGURACIÓN GENERAL DEL CLUB
# =====================
st.markdown("### ⚙️ Configuración General")

col1, col2, col3 = st.columns([2, 3, 1])

with col1:
    # Nombre del club (solo admin puede editar)
    if es_admin():
        nuevo_nombre_club = st.text_input(
            "🏟️ Nombre del Club",
            value=nombre_club,
            help="Solo administradores pueden cambiar el nombre del club",
            key="club_name_input"
        )
    else:
        st.text_input(
            "🏟️ Nombre del Club",
            value=nombre_club,
            disabled=True,
            help="Solo administradores pueden cambiar el nombre del club",
            key="club_name_disabled"
        )
        nuevo_nombre_club = nombre_club

with col2:
    # Cuerpo técnico unificado (temporal hasta seleccionar categoría)
    cuerpo_tecnico_temporal = st.text_area(
        "👥 Cuerpo Técnico",
        value="Selecciona una categoría para ver/editar el cuerpo técnico",
        height=60,
        disabled=True,
        help="El cuerpo técnico se carga según la categoría seleccionada",
        key="temp_staff_area"
    )

with col3:
    # Fecha del día
    fecha_actual = st.date_input(
        "📅 Fecha",
        value=datetime.date.today(),
        help="Fecha de referencia para la planificación",
        key="fecha_planif"
    )

# =====================
# FILA 2: PARÁMETROS DEL MICROCICLO
# =====================
st.markdown("### 📋 Selección de Microciclo")

col1, col2, col3 = st.columns(3)

with col1:
    # Temporada
    temporadas_unicas = df_temporadas["nombre"].unique().tolist()
    temporada_seleccionada = st.selectbox(
        "📆 Temporada",
        temporadas_unicas,
        help="Selecciona la temporada activa",
        key="sel_temporada"
    )

with col2:
    # Categoría (filtrada por temporada)
    df_temp_filtrada = df_temporadas[df_temporadas["nombre"] == temporada_seleccionada]
    categorias_disponibles = df_temp_filtrada["categoria"].unique().tolist()
    categoria_seleccionada = st.selectbox(
        "🏷️ Categoría",
        categorias_disponibles,
        help="Selecciona la categoría del equipo",
        key="sel_categoria"
    )

with col3:
    # Microciclo (filtrado por temporada y categoría)
    temp_row = df_temp_filtrada[df_temp_filtrada["categoria"] == categoria_seleccionada]
    if temp_row.empty:
        st.warning("No se encontró combinación válida")
        st.stop()
    
    id_temporada = temp_row.iloc[0]["id_temporada"]
    
    microciclos_filtrados = df_microciclos[
        (df_microciclos["id_temporada"] == id_temporada) &
        (df_microciclos["categoria"] == categoria_seleccionada)
    ]
    
    if microciclos_filtrados.empty:
        st.warning("No hay microciclos disponibles")
        st.stop()
    
    microciclo_nombre = st.selectbox(
        "🔄 Microciclo",
        microciclos_filtrados["nombre_microciclo"].tolist(),
        help="Selecciona el microciclo a planificar",
        key="sel_microciclo"
    )

# =====================
# ACTUALIZAR CUERPO TÉCNICO SEGÚN CATEGORÍA
# =====================
# Ahora que tenemos la categoría, cargar los datos reales
df_staff = pd.read_csv(staff_csv)
fila_categoria = df_staff[df_staff["categoria"] == categoria_seleccionada]

entrenador = fila_categoria["entrenador"].values[0] if not fila_categoria.empty else ""
staff = fila_categoria["staff"].values[0] if not fila_categoria.empty else ""
fecha_guardada = fila_categoria["fecha"].values[0] if not fila_categoria.empty else str(fecha_actual)

# Combinar entrenador y staff en un solo campo
cuerpo_tecnico_actual = f"{entrenador}\n{staff}" if entrenador or staff else ""

# Verificar permisos para editar
puede_editar_staff = es_admin() or (info_usuario['usuario'] == entrenador)

# Actualizar el campo de cuerpo técnico con los datos reales
st.markdown("### 👥 Información del Cuerpo Técnico")

if puede_editar_staff:
    cuerpo_tecnico_input = st.text_area(
        "Cuerpo Técnico (Entrenador y Staff)",
        value=cuerpo_tecnico_actual,
        height=80,
        help="Primera línea: Entrenador principal. Siguientes líneas: Staff técnico",
        key="staff_edit_area"
    )
    fecha_input = fecha_actual
else:
    st.text_area(
        "Cuerpo Técnico (Entrenador y Staff)",
        value=cuerpo_tecnico_actual,
        height=80,
        disabled=True,
        help="Solo el entrenador asignado o administradores pueden editar",
        key="staff_readonly_area"
    )
    st.caption("💡 No tienes permisos para editar el cuerpo técnico de esta categoría")
    cuerpo_tecnico_input = cuerpo_tecnico_actual
    fecha_input = fecha_guardada

# Separar entrenador y staff del texto combinado
lineas_cuerpo_tecnico = cuerpo_tecnico_input.strip().split('\n')
entrenador_input = lineas_cuerpo_tecnico[0] if lineas_cuerpo_tecnico else ""
staff_input = '\n'.join(lineas_cuerpo_tecnico[1:]) if len(lineas_cuerpo_tecnico) > 1 else ""

# =====================
# DETECCIÓN DE CAMBIOS Y BOTÓN DE GUARDADO
# =====================
hay_cambios_club = es_admin() and (nuevo_nombre_club != nombre_club)
hay_cambios_staff = puede_editar_staff and (
    (entrenador_input != entrenador) or 
    (staff_input != staff) or 
    (str(fecha_input) != str(fecha_guardada))
)

if hay_cambios_club or hay_cambios_staff:
    st.info("ℹ️ Hay cambios sin guardar en la configuración")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Guardar Configuración", type="primary", use_container_width=True, key="save_config_btn"):
            cambios_realizados = []
            
            try:
                # Guardar cambios en club
                if hay_cambios_club and es_admin():
                    df_club_nuevo = pd.DataFrame([[nuevo_nombre_club]], columns=["nombre_club"])
                    df_club_nuevo.to_csv(club_csv, index=False)
                    cambios_realizados.append("✅ Nombre del club")
                
                # Guardar cambios en staff
                if hay_cambios_staff and puede_editar_staff:
                    df_staff_nuevo = df_staff[df_staff["categoria"] != categoria_seleccionada]
                    nueva_fila = {
                        "categoria": categoria_seleccionada,
                        "entrenador": entrenador_input,
                        "staff": staff_input,
                        "fecha": fecha_input
                    }
                    df_staff_nuevo = pd.concat([df_staff_nuevo, pd.DataFrame([nueva_fila])], ignore_index=True)
                    df_staff_nuevo.to_csv(staff_csv, index=False)
                    cambios_realizados.append("✅ Datos del cuerpo técnico")
                
                if cambios_realizados:
                    st.success("🎉 Configuración guardada: " + ", ".join(cambios_realizados))
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

# =====================
# LÍNEA DIVISORIA
# =====================
st.markdown("---")

# =====================
# SISTEMA DE ELIMINACIÓN (COMPACTO)
# =====================
planif_csv = "data/planificacion_microciclos.csv"

try:
    df_planif = pd.read_csv(planif_csv)
    df_planif.columns = df_planif.columns.str.strip().str.lower()

    # Limpieza
    required_cols = ["id_temporada", "nombre_microciclo", "categoria"]
    df_planif = df_planif.dropna(subset=required_cols)
    df_planif = df_planif[
        (df_planif["id_temporada"].astype(str).str.lower().str.strip() != "nan") &
        (df_planif["nombre_microciclo"].astype(str).str.lower().str.strip() != "nan") &
        (df_planif["categoria"].astype(str).str.lower().str.strip() != "nan")
    ]

    # Normalización
    id_temp_str = normalize_for_matching(id_temporada)
    cat_str = normalize_for_matching(categoria_seleccionada)
    micro_str = normalize_for_matching(microciclo_nombre)

    # Matching
    df_planif_temp = df_planif.copy()
    df_planif_temp["id_temporada_norm"] = df_planif_temp["id_temporada"].apply(normalize_for_matching)
    df_planif_temp["categoria_norm"] = df_planif_temp["categoria"].apply(normalize_for_matching)
    df_planif_temp["nombre_microciclo_norm"] = df_planif_temp["nombre_microciclo"].apply(normalize_for_matching)

    coincidencias = df_planif_temp[
        (df_planif_temp["id_temporada_norm"] == id_temp_str) &
        (df_planif_temp["categoria_norm"] == cat_str) &
        (df_planif_temp["nombre_microciclo_norm"] == micro_str)
    ]
    
    micro_existente = len(coincidencias) > 0

    # Mostrar estado y botón de eliminación en una línea compacta
    if micro_existente:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"⚠️ Este microciclo tiene **{len(coincidencias)}** registros guardados")
        with col2:
            if es_admin():
                if st.button("🗑️ Eliminar microciclo", type="secondary", key="del_micro_btn"):
                    df_filtrado = df_planif.drop(coincidencias.index)
                    df_filtrado.to_csv(planif_csv, index=False)
                    st.success(f"✅ Microciclo eliminado")
                    st.rerun()
            else:
                st.caption("Solo admin puede eliminar")
    else:
        st.info("ℹ️ Este microciclo no tiene planificación guardada aún")

    # Debug info solo para admin (en expander compacto)
    if es_admin():
        with st.expander("🔍 Info técnica", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"ID Temp: {id_temporada} → {id_temp_str}")
            with col2:
                st.caption(f"Cat: {categoria_seleccionada} → {cat_str}")
            with col3:
                st.caption(f"Micro: {microciclo_nombre} → {micro_str}")

except FileNotFoundError:
    st.info("ℹ️ Primera vez - no existe archivo de planificación")
except Exception as e:
    st.error(f"❌ Error: {e}")

# =====================
# EDITOR Y RESUMEN (SIN CAMBIOS)
# =====================
mostrar_editor_microciclo(
    temporada=id_temporada,
    categoria=categoria_seleccionada,
    microciclo=microciclo_nombre,
    glosario_df=cargar_datos_csv("data/glosario_tactico.csv")
)

mostrar_resumen_microciclo(
    id_temporada,
    categoria_seleccionada,
    microciclo_nombre
)

# =====================
# EXPORTACIÓN PARA PLANIFICACIÓN
# =====================
def generar_pdf_planificacion():
    """Helper para generar PDF de planificación general"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte de Planificación General", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Club: {nombre_club}", ln=True)
    pdf.cell(0, 10, f"Temporada: {temporada_seleccionada}", ln=True)
    pdf.cell(0, 10, f"Categoría: {categoria_seleccionada}", ln=True)
    pdf.cell(0, 10, f"Microciclo: {microciclo_nombre}", ln=True)
    pdf.cell(0, 10, f"Entrenador: {entrenador}", ln=True)
    pdf.cell(0, 10, f"Fecha: {fecha_actual}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generado por: {info_usuario['nombre_completo']} ({info_usuario['rol']})", ln=True)
    
    return bytes(pdf.output(dest='S'))

def generar_excel_planificacion():
    """Helper para generar Excel de planificación general"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Datos generales
        info_general = pd.DataFrame([{
            "Club": nombre_club,
            "Temporada": temporada_seleccionada,
            "Categoría": categoria_seleccionada,
            "Microciclo": microciclo_nombre,
            "Entrenador": entrenador,
            "Fecha": fecha_actual,
            "Generado por": info_usuario['nombre_completo'],
            "Rol": info_usuario['rol']
        }])
        info_general.to_excel(writer, index=False, sheet_name="Info_General")
        
        # Microciclos disponibles
        microciclos_filtrados.to_excel(writer, index=False, sheet_name="Microciclos")
        
        # Temporadas
        df_temporadas.to_excel(writer, index=False, sheet_name="Temporadas")
    
    return buffer.getvalue()

# Botones de exportación
st.markdown("### 📤 Exportar Reporte de Planificación")
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Exportar PDF", type="primary", use_container_width=True, key="export_pdf_btn_planif"):
        pdf_data = generar_pdf_planificacion()
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_data,
            file_name=f"planificacion_{categoria_seleccionada}_{microciclo_nombre.replace(' ', '_')}.pdf",
            mime='application/pdf'
        )

with col2:
    if st.button("📊 Exportar Excel", type="primary", use_container_width=True, key="export_xlsx_btn_planif"):
        excel_data = generar_excel_planificacion()
        st.download_button(
            label="📥 Descargar Excel",
            data=excel_data,
            file_name=f"planificacion_{categoria_seleccionada}_{microciclo_nombre.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# =====================
# EDITOR AVANZADO (SOLO ADMIN)
# =====================
if es_admin():
    st.markdown("---")
    
    if st.checkbox("🛠️ **Abrir Editor Avanzado** (Limpieza y Edición)", 
                   key="check_editor_avanzado",
                   help="Herramientas avanzadas para administradores"):
        st.markdown("---")
        mostrar_editor_avanzado(
            id_temporada,
            categoria_seleccionada,
            microciclo_nombre
        )
else:
    st.markdown("---")
    st.caption("💡 El Editor Avanzado está disponible solo para administradores")