import streamlit as st
import pandas as pd
import os

# Cargar glosario táctico desde CSV
def cargar_glosario():
    ruta_glosario = os.path.join("data", "glosario_tactico.csv")
    if not os.path.exists(ruta_glosario):
        st.error("❌ No se encontró el archivo glosario_tactico.csv en la carpeta /data.")
        return pd.DataFrame()
    return pd.read_csv(ruta_glosario)

# Renderizar editor completo del microciclo
def render_editor_microciclo(micro):
    st.markdown("## ✍️ Editor Táctico del Microciclo")
    glosario = cargar_glosario()
    if glosario.empty:
        return

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    id_microciclo = micro["id_microciclo"]

    for i, dia in enumerate(dias_semana):
        with st.expander(f"📅 {dia}", expanded=(i == 0)):
            st.markdown("#### 🧱 Parte Situacional")
            seleccion_situacional = render_bloque_dia("Situacional", glosario, id_microciclo, dia)

            st.markdown("#### ⚙️ Parte Global")
            seleccion_global = render_bloque_dia("Global", glosario, id_microciclo, dia)

            st.markdown("#### 🏆 Parte Global Competitiva")
            seleccion_global_competitiva = render_bloque_dia("Global Competitiva", glosario, id_microciclo, dia)

# Renderiza cada bloque del día con recuperación automática desde CSV
def render_bloque_dia(nombre_bloque, glosario, id_microciclo, dia_nombre):
    opciones = sorted(glosario["principio"].unique())
    ruta_planificacion = os.path.join("data", "planificacion_microciclos.csv")
    default_seleccionados = []

    if os.path.exists(ruta_planificacion):
        try:
            df_plan = pd.read_csv(ruta_planificacion)
            filtro = (
                (df_plan["id_microciclo"] == id_microciclo) &
                (df_plan["dia"] == dia_nombre) &
                (df_plan["bloque"] == nombre_bloque)
            )
            fila = df_plan[filtro]
            if not fila.empty:
                default_seleccionados = fila["principios"].values[0].split(", ")
        except Exception as e:
            st.warning(f"⚠️ Error al cargar planificación previa: {e}")

    key_widget = f"{id_microciclo}_{dia_nombre}_{nombre_bloque}"

    seleccionados = st.multiselect(
        f"Selecciona principios para {nombre_bloque} ({dia_nombre})",
        opciones,
        default=default_seleccionados,
        key=key_widget
    )

    return seleccionados
