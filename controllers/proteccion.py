# controllers/proteccion.py

import streamlit as st

def verificar_acceso(roles_permitidos=None):
    """
    Verifica que el usuario esté autenticado y tenga los permisos necesarios.
    
    Args:
        roles_permitidos: Lista de roles que pueden acceder (None = cualquier usuario autenticado)
    """
    # Verificar si el usuario está autenticado
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("❌ Acceso denegado. Por favor inicie sesión.")
        st.stop()
        return False
    
    # Si no se especifican roles, solo requiere autenticación
    if roles_permitidos is None:
        return True
    
    # Verificar que el usuario tenga uno de los roles permitidos
    usuario_rol = st.session_state.get('rol', None)
    
    if usuario_rol not in roles_permitidos:
        st.error(f"❌ Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(roles_permitidos)}")
        st.warning(f"Tu rol actual es: **{usuario_rol}**")
        
        # Botón para volver al login
        if st.button("🔙 Volver al inicio"):
            # Limpiar sesión
            for key in ['authenticated', 'usuario', 'rol', 'nombre_completo', 'email']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("app.py")
        
        st.stop()
        return False
    
    return True

def obtener_info_usuario():
    """
    Obtiene la información del usuario actual de la sesión.
    
    Returns:
        dict: Información del usuario o None si no está autenticado
    """
    if not st.session_state.get('authenticated', False):
        return None
    
    return {
        'usuario': st.session_state.get('usuario', 'Desconocido'),
        'rol': st.session_state.get('rol', 'sin_rol'),
        'nombre_completo': st.session_state.get('nombre_completo', 'Usuario'),
        'email': st.session_state.get('email', '')
    }

def mostrar_info_usuario_sidebar():
    """
    Muestra la información del usuario en el sidebar.
    """
    info_usuario = obtener_info_usuario()
    
    if info_usuario:
        with st.sidebar:
            st.markdown("### 👤 Usuario Actual")
            st.markdown(f"**{info_usuario['nombre_completo']}**")
            st.caption(f"@{info_usuario['usuario']}")
            st.caption(f"Rol: {info_usuario['rol']}")
            
            st.markdown("---")
            
            # Botón de cerrar sesión
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                # Limpiar toda la sesión
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("app.py")

def es_admin():
    return st.session_state.get("rol") == "admin"

def es_entrenador():
    """
    Verifica si el usuario actual es entrenador.
    
    Returns:
        bool: True si es entrenador, False en caso contrario
    """
    return st.session_state.get('rol', '') == 'entrenador'

def es_visor():
    """
    Verifica si el usuario actual es visor.
    
    Returns:
        bool: True si es visor, False en caso contrario
    """
    return st.session_state.get('rol', '') == 'visor'

def requiere_admin():
    """
    Decorator para funciones que requieren rol de administrador.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not es_admin():
                st.error("❌ Esta función requiere permisos de administrador")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Función para mostrar menú según rol
def mostrar_menu_por_rol():
    """
    Muestra opciones de menú basadas en el rol del usuario.
    """
    rol = st.session_state.get('rol', 'visor')
    
    with st.sidebar:
        st.markdown("### 📋 Menú")
        
        if rol == 'admin':
            opciones = [
                "🏠 Inicio",
                "📋 Planificación",
                "👥 Gestión Usuarios",
                "⚙️ Configuración",
                "📊 Reportes"
            ]
        elif rol == 'entrenador':
            opciones = [
                "🏠 Inicio",
                "📋 Planificación",
                "📊 Mis Reportes"
            ]
        else:  # visor
            opciones = [
                "🏠 Inicio",
                "📊 Ver Planificaciones"
            ]
        
        seleccion = st.radio("Selecciona:", opciones, label_visibility="collapsed")
        
        return seleccion