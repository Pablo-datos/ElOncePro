# Archivo: utils/editor_tactico.py
import streamlit as st
import pandas as pd

def render_editor_microciclo():
    st.subheader("📆 Editor de Microciclo Táctico")

    # Cargar CSVs
    microciclos_df = pd.read_csv("data/microciclos.csv")
    temporadas_df = pd.read_csv("data/temporadas.csv")

    # Mostrar información general
    st.markdown("### ⚖️ Selección de Temporada y Categoría")

    temporada_nombres = temporadas_df['nombre'].unique()
    temporada_seleccionada = st.selectbox("Selecciona la temporada", temporada_nombres)

    categorias_temporada = temporadas_df[temporadas_df['nombre'] == temporada_seleccionada]['categoria'].unique()
    categoria_seleccionada = st.selectbox("Selecciona la categoría", categorias_temporada)

    # Obtener ID temporada seleccionada
    temporada_id = temporadas_df[
        (temporadas_df['nombre'] == temporada_seleccionada) &
        (temporadas_df['categoria'] == categoria_seleccionada)
    ]['id_temporada'].values[0]

    # Mostrar microciclos filtrados
    microciclos_filtrados = microciclos_df[(microciclos_df['id_temporada'] == temporada_id) &
                                           (microciclos_df['categoria'] == categoria_seleccionada)]

    if microciclos_filtrados.empty:
        st.warning("No hay microciclos para esta combinación.")
        return

    microciclo_nombres = microciclos_filtrados['nombre_microciclo'].tolist()
    microciclo_seleccionado = st.selectbox("Selecciona el microciclo", microciclo_nombres)

    # Mostrar resumen
    st.markdown("---")
    st.markdown(f"### 🔹 Microciclo: `{microciclo_seleccionado}`")

    microciclo_row = microciclos_filtrados[microciclos_filtrados['nombre_microciclo'] == microciclo_seleccionado].iloc[0]
    st.markdown(f"- 🗓️ **Inicio:** {microciclo_row['fecha_inicio']}")
    st.markdown(f"- 📅 **Fin:** {microciclo_row['fecha_fin']}")
    st.markdown(f"- 🏀 **Categoría:** {microciclo_row['categoria']}")
    st.markdown("---")

    # Placeholder para el editor diario (puedes conectar aquí tu editor por días)
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    for dia in dias_semana:
        with st.expander(f"🗓️ {dia}"):
            st.write(f"Editor del día **{dia}** (a integrar en la siguiente fase)")
