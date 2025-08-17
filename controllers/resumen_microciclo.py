import streamlit as st
import pandas as pd
import os
import plotly.express as px
from fpdf import FPDF
import io
from controllers.proteccion import es_admin, es_entrenador, es_visor, obtener_info_usuario

PLANIFICACION_CSV = "data/planificacion_microciclos.csv"

def mostrar_resumen_microciclo(id_temporada, categoria, nombre_microciclo):
    """
    Muestra resumen del microciclo con control de exportación según rol
    """
    if not os.path.exists(PLANIFICACION_CSV):
        st.warning("No hay planificación guardada todavía.")
        return

    df = pd.read_csv(PLANIFICACION_CSV)

    df_filtrado = df[
        (df["id_temporada"] == id_temporada) &
        (df["categoria"] == categoria) &
        (df["nombre_microciclo"] == nombre_microciclo)
    ].sort_values(by=["dia", "bloque"])

    if df_filtrado.empty:
        st.info("Este microciclo no tiene principios tácticos guardados aún.")
        return

    st.markdown("### 📊 Resumen del Microciclo Actual")
    st.dataframe(df_filtrado[["dia", "bloque", "principios"]], use_container_width=True)

    # 📈 Gráfico con Plotly Express
    st.markdown("### 📈 Principios más utilizados en el microciclo (interactivo)")
    principios_series = df_filtrado["principios"].dropna().str.split(", ").explode()
    conteo_principios = principios_series.value_counts().reset_index()
    conteo_principios.columns = ["Principio", "Frecuencia"]

    if conteo_principios.empty:
        st.info("No hay suficientes datos para generar el gráfico.")
        return

    fig = px.bar(
        conteo_principios,
        x="Frecuencia",
        y="Principio",
        orientation="h",
        color="Frecuencia",
        color_continuous_scale="Blues",
        title="Principios tácticos más utilizados"
    )
    fig.update_layout(yaxis_title="", xaxis_title="Frecuencia", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # =====================
    # CONTROL DE EXPORTACIÓN POR ROL
    # =====================
    
    # Verificar permisos de exportación
    puede_exportar = False
    mensaje_exportacion = ""
    
    if es_admin():
        puede_exportar = True
        mensaje_exportacion = "✅ Como administrador, puedes exportar todos los datos."
    elif es_entrenador():
        # Verificar si el entrenador está asignado a esta categoría
        info_usuario = obtener_info_usuario()
        df_staff = pd.read_csv("data/staff_por_categoria.csv")
        fila_staff = df_staff[df_staff["categoria"] == categoria]
        
        if not fila_staff.empty:
            entrenador_asignado = fila_staff["entrenador"].values[0]
            # Comparar con el nombre completo o usuario
            if (info_usuario['usuario'] == entrenador_asignado or 
                info_usuario['nombre_completo'] == entrenador_asignado):
                puede_exportar = True
                mensaje_exportacion = "✅ Puedes exportar este microciclo porque estás asignado a esta categoría."
            else:
                puede_exportar = False
                mensaje_exportacion = "⚠️ Solo puedes exportar microciclos de categorías donde estés asignado como entrenador."
        else:
            puede_exportar = True  # Si no hay entrenador asignado, permitir
            mensaje_exportacion = "✅ Puedes exportar este microciclo."
    elif es_visor():
        puede_exportar = False
        mensaje_exportacion = "❌ Los usuarios con rol de visor no pueden exportar datos."
    else:
        puede_exportar = False
        mensaje_exportacion = "❌ No tienes permisos para exportar."

    # Mostrar sección de exportación solo si tiene permisos
    if puede_exportar:
        st.markdown("### 📤 Exportar planificación")
        st.info(mensaje_exportacion)
        
        # Preparar datos para exportación
        df_staff = pd.read_csv("data/staff_por_categoria.csv")
        fila_staff = df_staff[df_staff["categoria"] == categoria]

        entrenador = fila_staff["entrenador"].values[0] if not fila_staff.empty else "N/D"
        staff = fila_staff["staff"].values[0] if not fila_staff.empty else "N/D"
        fecha = fila_staff["fecha"].values[0] if not fila_staff.empty else "N/D"

        df_export = df_filtrado[["dia", "bloque", "principios"]].copy()
        df_export.columns = ["Día", "Bloque", "Principios tácticos"]

        col1, col2 = st.columns(2)
        
        with col1:
            # Exportar a Excel
            nombre_excel = f"planificacion_{categoria}_{nombre_microciclo.replace(' ', '_')}.xlsx"
            if st.button("📊 Exportar a Excel", type="primary", use_container_width=True, key="export_excel_resumen_btn"):
                buffer = io.BytesIO()

                encabezado = pd.DataFrame([{
                    "Categoría": categoria,
                    "Entrenador": entrenador,
                    "Staff": staff,
                    "Fecha": fecha,
                    "Exportado por": obtener_info_usuario()['nombre_completo'],
                    "Rol": obtener_info_usuario()['rol']
                }])

                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    # Hoja de encabezado
                    encabezado.to_excel(writer, index=False, sheet_name="Información")
                    
                    # Hoja de microciclo
                    df_export.to_excel(writer, index=False, sheet_name="Microciclo")
                    
                    # Hoja de estadísticas
                    conteo_principios.to_excel(writer, index=False, sheet_name="Estadísticas")

                st.download_button(
                    label="📥 Descargar Excel",
                    data=buffer.getvalue(),
                    file_name=nombre_excel,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with col2:
            # Exportar a PDF
            if st.button("📄 Exportar a PDF", type="primary", use_container_width=True):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                # Título
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Planificación del Microciclo", ln=True, align="C")

                # Información del microciclo
                pdf.set_font("Arial", '', 12)
                pdf.ln(10)
                pdf.cell(0, 10, f"Categoría: {categoria}", ln=True)
                pdf.cell(0, 10, f"Microciclo: {nombre_microciclo}", ln=True)
                pdf.cell(0, 10, f"Entrenador: {entrenador}", ln=True)
                pdf.cell(0, 10, f"Staff técnico: {staff}", ln=True)
                pdf.cell(0, 10, f"Fecha: {fecha}", ln=True)
                
                # Información de exportación
                pdf.ln(5)
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 10, f"Exportado por: {obtener_info_usuario()['nombre_completo']} ({obtener_info_usuario()['rol']})", ln=True)
                
                # Tabla de datos
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(40, 10, "Día", 1)
                pdf.cell(50, 10, "Bloque", 1)
                pdf.cell(100, 10, "Principios tácticos", 1)
                pdf.ln()

                pdf.set_font("Arial", '', 11)
                for _, row in df_export.iterrows():
                    pdf.cell(40, 10, str(row["Día"]), 1)
                    pdf.cell(50, 10, str(row["Bloque"]), 1)
                    
                    # Manejar texto largo en principios
                    principios_text = str(row["Principios tácticos"])
                    if len(principios_text) > 50:
                        # Dividir en líneas
                        y_before = pdf.get_y()
                        pdf.multi_cell(100, 10, principios_text, 1)
                        y_after = pdf.get_y()
                        pdf.set_xy(pdf.get_x(), y_after)
                    else:
                        pdf.cell(100, 10, principios_text, 1)
                        pdf.ln()

                # Añadir página de estadísticas
                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, "Estadísticas del Microciclo", ln=True, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", '', 11)
                pdf.cell(0, 10, f"Total de días planificados: {df_filtrado['dia'].nunique()}", ln=True)
                pdf.cell(0, 10, f"Total de bloques utilizados: {df_filtrado['bloque'].nunique()}", ln=True)
                pdf.cell(0, 10, f"Total de principios únicos: {conteo_principios['Principio'].nunique()}", ln=True)
                
                # Top 5 principios
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Top 5 Principios Más Utilizados:", ln=True)
                pdf.set_font("Arial", '', 11)
                
                for i, row in conteo_principios.head(5).iterrows():
                    pdf.cell(0, 10, f"{i+1}. {row['Principio']} - {row['Frecuencia']} veces", ln=True)

                nombre_pdf = f"planificacion_{categoria}_{nombre_microciclo.replace(' ', '_')}.pdf"
                pdf_bytes = bytes(pdf.output(dest='S'))

                st.download_button(
                    label="📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=nombre_pdf,
                    mime='application/pdf'
                )
    
    else:
        # Mostrar mensaje si no puede exportar
        st.markdown("### 📤 Exportación")
        st.warning(mensaje_exportacion)
        
        if es_visor():
            st.info("💡 Si necesitas exportar estos datos, contacta con un administrador o entrenador.")
        elif es_entrenador():
            st.info("💡 Solo puedes exportar microciclos de las categorías donde estés asignado como entrenador.")

# Función adicional para exportación masiva (solo admin)
def exportar_todo_sistema():
    """
    Exporta todos los datos del sistema (solo para administradores)
    """
    if not es_admin():
        st.error("❌ Esta función solo está disponible para administradores.")
        return None
    
    try:
        # Crear un archivo Excel con múltiples hojas
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            # Hoja 1: Toda la planificación
            if os.path.exists(PLANIFICACION_CSV):
                df_planif = pd.read_csv(PLANIFICACION_CSV)
                df_planif.to_excel(writer, index=False, sheet_name="Planificación_Completa")
            
            # Hoja 2: Temporadas
            if os.path.exists("data/temporadas.csv"):
                df_temp = pd.read_csv("data/temporadas.csv")
                df_temp.to_excel(writer, index=False, sheet_name="Temporadas")
            
            # Hoja 3: Microciclos
            if os.path.exists("data/microciclos.csv"):
                df_micro = pd.read_csv("data/microciclos.csv")
                df_micro.to_excel(writer, index=False, sheet_name="Microciclos")
            
            # Hoja 4: Staff
            if os.path.exists("data/staff_por_categoria.csv"):
                df_staff = pd.read_csv("data/staff_por_categoria.csv")
                df_staff.to_excel(writer, index=False, sheet_name="Staff")
            
            # Hoja 5: Información de exportación
            info_export = pd.DataFrame([{
                "Fecha de exportación": pd.Timestamp.now(),
                "Exportado por": obtener_info_usuario()['nombre_completo'],
                "Rol": obtener_info_usuario()['rol'],
                "Tipo": "Exportación completa del sistema"
            }])
            info_export.to_excel(writer, index=False, sheet_name="Info_Exportación")
        
        return buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error al exportar: {str(e)}")
        return None