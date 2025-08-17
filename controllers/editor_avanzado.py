# controllers/editor_avanzado.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from controllers.planificador import (
    normalize_for_matching,
    crear_backup,
    guardar_planificacion_inteligente,
    limpiar_y_migrar_datos,
)
from controllers.proteccion import es_admin, obtener_info_usuario

def mostrar_editor_avanzado(id_temporada, categoria, microciclo_nombre):
    """
    Módulo de edición avanzada para limpieza y modificación de microciclos.
    SOLO PARA ADMINISTRADORES
    """
    # Verificación adicional de seguridad
    if not es_admin():
        st.error("❌ No tienes permisos para acceder al Editor Avanzado")
        st.warning("Esta herramienta está disponible solo para administradores.")
        return
    
    st.markdown("### 🧹 Limpieza y Edición Avanzada")
    st.info("Modifica o elimina elementos específicos del microciclo actual")
    
    # Mostrar usuario que está realizando las acciones
    info_usuario = obtener_info_usuario()
    st.caption(f"👤 Editando como: {info_usuario['nombre_completo']} (Admin)")
    
    PLANIFICACION_CSV = "data/planificacion_microciclos.csv"

    # Botón de limpieza de datos (solo admin)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔧 Verificar y limpiar datos", type="primary", use_container_width=True):
            with st.spinner("Limpiando datos..."):
                success, mensaje = limpiar_y_migrar_datos()
                if success:
                    st.success(f"✅ {mensaje}")
                    # Log de auditoría
                    st.caption(f"Limpieza ejecutada por {info_usuario['usuario']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")

    try:
        df_planif = pd.read_csv(PLANIFICACION_CSV)
        df_planif.columns = df_planif.columns.str.strip().str.lower()

        id_temp_str = normalize_for_matching(id_temporada)
        cat_str = normalize_for_matching(categoria)
        micro_str = normalize_for_matching(microciclo_nombre)

        df_planif_temp = df_planif.copy()
        df_planif_temp["id_temporada_norm"] = df_planif_temp["id_temporada"].apply(normalize_for_matching)
        df_planif_temp["categoria_norm"] = df_planif_temp["categoria"].apply(normalize_for_matching)
        df_planif_temp["nombre_microciclo_norm"] = df_planif_temp["nombre_microciclo"].apply(normalize_for_matching)

        mask_microciclo = (
            (df_planif_temp["id_temporada_norm"] == id_temp_str) &
            (df_planif_temp["categoria_norm"] == cat_str) &
            (df_planif_temp["nombre_microciclo_norm"] == micro_str)
        )

        indices_microciclo = df_planif_temp[mask_microciclo].index
        df_microciclo = df_planif.loc[indices_microciclo].copy()

        if df_microciclo.empty:
            st.warning("No se encontraron datos para este microciclo")
            return

    except FileNotFoundError:
        st.error("❌ No se encontró el archivo de planificación")
        return
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return

    # Tabs con advertencias de seguridad
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗑️ Eliminar Día", 
        "✏️ Editar Principios", 
        "📊 Estadísticas",
        "🔍 Auditoría"
    ])

    with tab1:
        st.markdown("#### 🗑️ Eliminar día completo")
        st.warning("⚠️ **ADVERTENCIA**: Esta acción es IRREVERSIBLE. Se creará un backup automático.")
        
        dias = sorted(df_microciclo['dia'].dropna().unique())
        if dias:
            dia_seleccionado = st.selectbox("Día a eliminar:", dias)
            
            # Mostrar preview de lo que se eliminará
            df_preview = df_microciclo[df_microciclo['dia'] == dia_seleccionado]
            st.info(f"Se eliminarán {len(df_preview)} registros del día {dia_seleccionado}")
            
            with st.expander("Ver detalles de lo que se eliminará"):
                st.dataframe(df_preview[['dia', 'bloque', 'principio']], use_container_width=True)
            
            # Confirmación doble
            confirmar1 = st.checkbox(f"Confirmo que quiero eliminar el día {dia_seleccionado}")
            
            if confirmar1:
                confirmar2 = st.checkbox("⚠️ SEGUNDA CONFIRMACIÓN: Entiendo que esta acción no se puede deshacer")
                
                if confirmar2:
                    if st.button("🗑️ ELIMINAR DÍA DEFINITIVAMENTE", type="primary"):
                        try:
                            # Crear backup con información del usuario
                            backup_path = crear_backup(PLANIFICACION_CSV)
                            
                            indices = df_preview.index
                            df_nuevo = df_planif.drop(indices)
                            df_nuevo.to_csv(PLANIFICACION_CSV, index=False)
                            
                            st.success(f"✅ Día '{dia_seleccionado}' eliminado correctamente.")
                            st.info(f"📦 Backup creado en: {backup_path}")
                            st.caption(f"Eliminado por: {info_usuario['nombre_completo']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Log para auditoría
                            guardar_log_auditoria(
                                accion="Eliminar día",
                                detalles=f"Día {dia_seleccionado} del microciclo {microciclo_nombre}",
                                usuario=info_usuario['usuario']
                            )
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        else:
            st.info("No hay días para mostrar")

    with tab2:
        st.markdown("#### ✏️ Editar principios tácticos")
        st.info("Los cambios se guardarán con registro de auditoría")
        
        dias = sorted(df_microciclo['dia'].dropna().unique())
        if dias:
            col1, col2 = st.columns(2)
            
            with col1:
                dia = st.selectbox("Día", dias)
            
            with col2:
                bloques = sorted(df_microciclo[df_microciclo["dia"] == dia]["bloque"].dropna().unique())
                bloque = st.selectbox("Bloque", bloques)
            
            actuales = df_microciclo[
                (df_microciclo["dia"] == dia) & (df_microciclo["bloque"] == bloque)
            ]["principio"].dropna().tolist()

            st.markdown("**Principios actuales:**")
            if actuales:
                for i, p in enumerate(actuales, 1):
                    st.write(f"{i}. {p}")
            else:
                st.write("*Sin principios*")

            # Editor con validación
            nuevos = st.text_area(
                "Editar principios (separados por coma)", 
                value=", ".join(actuales),
                help="Separa cada principio con una coma"
            )
            lista_nuevos = [p.strip() for p in nuevos.split(",") if p.strip()]

            # Mostrar cambios
            if set(lista_nuevos) != set(actuales):
                st.markdown("**Cambios detectados:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    eliminados = set(actuales) - set(lista_nuevos)
                    if eliminados:
                        st.markdown("❌ **Se eliminarán:**")
                        for p in eliminados:
                            st.write(f"- {p}")
                
                with col2:
                    agregados = set(lista_nuevos) - set(actuales)
                    if agregados:
                        st.markdown("✅ **Se agregarán:**")
                        for p in agregados:
                            st.write(f"- {p}")

                if st.button("💾 Guardar Cambios", type="primary"):
                    success, msg = guardar_planificacion_inteligente(
                        id_temporada, categoria, microciclo_nombre, dia, bloque, lista_nuevos
                    )
                    if success:
                        st.success(msg)
                        st.caption(f"Modificado por: {info_usuario['nombre_completo']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Log para auditoría
                        guardar_log_auditoria(
                            accion="Editar principios",
                            detalles=f"{dia}/{bloque} - {len(actuales)} → {len(lista_nuevos)} principios",
                            usuario=info_usuario['usuario']
                        )
                        
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.info("No hay cambios para guardar")
        else:
            st.info("No hay datos disponibles para editar")

    with tab3:
        st.markdown("#### 📊 Estadísticas del microciclo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Total principios", len(df_microciclo))
        with col2:
            st.metric("📅 Días únicos", df_microciclo["dia"].nunique())
        with col3:
            st.metric("📦 Bloques únicos", df_microciclo["bloque"].nunique())
        with col4:
            st.metric("🎯 Principios únicos", df_microciclo["principio"].nunique())

        st.markdown("---")
        st.markdown("**Distribución por día:**")
        df_dist = df_microciclo.groupby("dia")["principio"].count().reset_index(name="Cantidad")
        
        # Gráfico de barras
        st.bar_chart(df_dist.set_index("dia")["Cantidad"])
        
        # Tabla detallada
        with st.expander("Ver tabla detallada"):
            st.dataframe(df_dist, use_container_width=True, hide_index=True)
        
        # Análisis de bloques
        st.markdown("**Distribución por bloque:**")
        df_bloques = df_microciclo.groupby("bloque")["principio"].count().reset_index(name="Cantidad")
        st.dataframe(df_bloques, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("#### 🔍 Registro de Auditoría")
        st.info("Historial de cambios realizados en el Editor Avanzado")
        
        # Cargar logs si existen
        logs = cargar_logs_auditoria()
        
        if logs:
            # Filtrar por este microciclo si es posible
            df_logs = pd.DataFrame(logs)
            
            # Mostrar logs más recientes primero
            df_logs = df_logs.sort_values('timestamp', ascending=False)
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                usuarios_unicos = df_logs['usuario'].unique()
                usuario_filtro = st.selectbox(
                    "Filtrar por usuario",
                    ["Todos"] + list(usuarios_unicos)
                )
            
            with col2:
                acciones_unicas = df_logs['accion'].unique()
                accion_filtro = st.selectbox(
                    "Filtrar por acción",
                    ["Todas"] + list(acciones_unicas)
                )
            
            # Aplicar filtros
            df_mostrar = df_logs.copy()
            if usuario_filtro != "Todos":
                df_mostrar = df_mostrar[df_mostrar['usuario'] == usuario_filtro]
            if accion_filtro != "Todas":
                df_mostrar = df_mostrar[df_mostrar['accion'] == accion_filtro]
            
            # Mostrar tabla
            st.dataframe(
                df_mostrar[['timestamp', 'usuario', 'accion', 'detalles']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": "Fecha/Hora",
                    "usuario": "Usuario",
                    "accion": "Acción",
                    "detalles": "Detalles"
                }
            )
            
            # Exportar logs (solo admin)
            if st.button("📥 Exportar logs completos", disabled=not es_admin()):
                df_export = pd.DataFrame(logs)
                csv = df_export.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"auditoria_editor_avanzado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No hay registros de auditoría disponibles")

# Funciones auxiliares de auditoría
def guardar_log_auditoria(accion, detalles, usuario):
    """Guarda un registro de auditoría"""
    log_file = "data/logs_editor_avanzado.csv"
    
    nuevo_log = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'usuario': usuario,
        'accion': accion,
        'detalles': detalles
    }
    
    try:
        if os.path.exists(log_file):
            df_logs = pd.read_csv(log_file)
        else:
            df_logs = pd.DataFrame(columns=['timestamp', 'usuario', 'accion', 'detalles'])
        
        df_logs = pd.concat([df_logs, pd.DataFrame([nuevo_log])], ignore_index=True)
        df_logs.to_csv(log_file, index=False)
        
    except Exception as e:
        print(f"Error al guardar log: {e}")

def cargar_logs_auditoria():
    """Carga los logs de auditoría"""
    log_file = "data/logs_editor_avanzado.csv"
    
    try:
        if os.path.exists(log_file):
            df_logs = pd.read_csv(log_file)
            return df_logs.to_dict('records')
        return []
    except:
        return []