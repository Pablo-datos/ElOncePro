import streamlit as st
import pandas as pd
import os
import sys

# Paso 3: Añadir el path raíz para evitar errores con imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils import cargar_datos_csv, obtener_microciclos_disponibles
from controllers.planificador import guardar_planificacion

# Función principal para mostrar la planificación de fútbol
def mostrar_planificacion_futbol():
    st.title("Planificación Táctica Semanal – Fútbol")

    # Cargar datasets base
    temporadas_df = cargar_datos_csv("data/temporadas.csv")
    microciclos_df = cargar_datos_csv("data/microciclos.csv")
    glosario_df = cargar_datos_csv("data/glosario_tactico.csv")

    if temporadas_df.empty or microciclos_df.empty or glosario_df.empty:
        st.error("No se pudieron cargar los archivos necesarios.")
        return

    # Selección de temporada y categoría
    temporada = st.selectbox("Selecciona una temporada:", temporadas_df["nombre"].unique())
    categorias = temporadas_df[temporadas_df["nombre"] == temporada]["categoria"].unique()
    categoria = st.selectbox("Selecciona una categoría:", categorias)

    # Filtrar microciclos disponibles
    microciclos_disponibles = obtener_microciclos_disponibles(microciclos_df, temporada, categoria)
    if not microciclos_disponibles:
        st.warning("No hay microciclos disponibles para esta combinación.")
        return

    nombre_microciclo = st.selectbox("Selecciona un microciclo:", microciclos_disponibles)

    # Filtrar microciclo seleccionado
    microciclo_seleccionado = microciclos_df[
        (microciclos_df["nombre_microciclo"] == nombre_microciclo) &
        (microciclos_df["categoria"] == categoria) &
        (microciclos_df["id_temporada"] == temporadas_df[temporadas_df["nombre"] == temporada]["id_temporada"].values[0])
    ]

    if microciclo_seleccionado.empty:
        st.error("No se encontró el microciclo seleccionado.")
        return

    fecha_inicio = pd.to_datetime(microciclo_seleccionado["fecha_inicio"].values[0])
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    st.markdown("---")

    # Mostrar planificación por día
    planificacion = {}
    for i, dia in enumerate(dias_semana):
        with st.expander(f"{dia} – {fecha_inicio.date() + pd.Timedelta(days=i)}"):
            bloques = ["Situacional", "Global", "Global Competitiva"]
            planificacion[dia] = {}
            for bloque in bloques:
                st.markdown(f"**Bloque {bloque}**")
                opciones = glosario_df["nombre_principio"].dropna().unique().tolist()
                seleccion = st.multiselect(f"Selecciona principios tácticos ({bloque})", opciones, key=f"{dia}_{bloque}")
                planificacion[dia][bloque] = seleccion

    st.markdown("---")

    # Botón de guardado
    if st.button("💾 Guardar planificación semanal"):
        guardar_planificacion(planificacion, temporada, categoria, nombre_microciclo)
        st.success("✅ Planificación guardada correctamente.")

