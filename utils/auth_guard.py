import streamlit as st

def requiere_autenticacion(rol_permitido=None):
    """
    Decorador para proteger funciones de Streamlit según autenticación y rol.
    - rol_permitido: Lista de roles permitidos (ej: ["admin", "staff"])
    """
    def wrapper(func):
        def inner(*args, **kwargs):
            if not st.session_state.get("autenticado", False):
                st.error("🔒 Acceso denegado. Inicia sesión para continuar.")
                st.stop()
            if rol_permitido and st.session_state.get("rol") not in rol_permitido:
                st.error("🚫 No tienes permisos para ver esta página.")
                st.stop()
            return func(*args, **kwargs)
        return inner
    return wrapper
