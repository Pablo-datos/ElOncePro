# app.py

import streamlit as st
import os
import sys
import pathlib

# Import hardening - PASO 4 adelantado para evitar problemas
BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from controllers.auth import validar_credenciales, inicializar_sistema_usuarios, crear_usuario

# Configuración de la página con branding El Once Pro
st.set_page_config(
    page_title="El Once Pro",
    page_icon="assets/logo_icon.png" if os.path.exists("assets/logo_icon.png") else "⚽",
    layout="centered"
)

# === Estilo global: fondo negro + texto blanco (El Once Pro) ===
st.markdown("""
<style>
  body, .stApp { background-color: #000000 !important; color: white !important; }
  .stButton > button { width: 100%; }
  /* Estilo adicional para inputs en tema oscuro */
  .stTextInput > div > div > input {
    background-color: #1a1a1a !important;
    color: white !important;
  }
  .stSelectbox > div > div > div {
    background-color: #1a1a1a !important;
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)

# Inicializar sistema de usuarios al arrancar
inicializar_sistema_usuarios()

# =====================
# LOGO EN SIDEBAR Y NAVEGACIÓN
# =====================
LOGO_DIR = "assets"
LOGO_PATH = os.path.join(LOGO_DIR, "logo_horizontal.png")

with st.sidebar:
    if st.session_state.get("authenticated", False):
        # Ocultar navegación automática de Streamlit
        st.markdown("<style>[data-testid='stSidebarNav']{display:none !important;}</style>", unsafe_allow_html=True)
        
        # Logo
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        st.markdown("### **El Once Pro**")
        st.markdown("---")
        
        # Menú de navegación personalizado
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
    else:
        # Mantener branding del login sin cambios
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, use_container_width=True)
        st.markdown("### **El Once Pro**")
        st.markdown("---")
        st.caption("Sistema de Planificación Táctica")

# =====================
# ESTILO CSS PERSONALIZADO
# =====================
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# =====================
# INTERFAZ DE LOGIN
# =====================
# Logo o título centrado
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Mostrar logo si existe
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.title("⚽ El Once Pro")
    st.markdown("### 🔐 Inicio de Sesión")

st.markdown("---")

# Formulario de login
with st.form("login_form"):
    username = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
    password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingrese su contraseña")
    
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("🔓 Iniciar Sesión", type="primary")
    with col2:
        info = st.form_submit_button("ℹ️ Información")

# Procesar login
if submit:
    if not username or not password:
        st.error("❌ Por favor complete todos los campos")
    else:
        # Validar credenciales con el nuevo sistema
        valido, mensaje, datos_usuario = validar_credenciales(username, password)
        
        if valido:
            # Guardar información en session state
            st.session_state["authenticated"] = True
            st.session_state["usuario"] = datos_usuario['usuario']
            st.session_state["rol"] = datos_usuario['rol']
            st.session_state["nombre_completo"] = datos_usuario['nombre_completo']
            st.session_state["email"] = datos_usuario.get('email', '')
            
            # Mensaje de bienvenida
            st.success(f"✅ ¡Bienvenido, {datos_usuario['nombre_completo']}!")
            st.balloons()
            
            # Redireccionar según el rol
            if datos_usuario['rol'] == 'admin':
                st.switch_page("pages/planificacion.py")
            elif datos_usuario['rol'] == 'entrenador':
                st.switch_page("pages/planificacion.py")
            else:  # visor u otros roles
                st.switch_page("pages/vista_planificacion.py")  # Crear esta página si no existe
        else:
            st.error(f"❌ {mensaje}")

# Mostrar información
if info:
    st.info("""
    **Credenciales por defecto:**
    - Usuario: `admin`
    - Contraseña: `admin123`
    
    **Roles disponibles:**
    - `admin`: Acceso completo
    - `entrenador`: Acceso a planificación
    - `visor`: Solo lectura
    """)

# =====================
# REGISTRO NUEVO (Solo para admins o primera configuración)
# =====================
with st.expander("🆕 Registro de nuevo usuario"):
    st.warning("⚠️ Solo administradores pueden crear nuevos usuarios")
    
    # Verificar si hay sesión de admin temporal para crear usuarios
    admin_temp_user = st.text_input("Usuario Admin", key="admin_user")
    admin_temp_pass = st.text_input("Contraseña Admin", type="password", key="admin_pass")
    
    if admin_temp_user and admin_temp_pass:
        # Validar que es admin
        valido, _, datos = validar_credenciales(admin_temp_user, admin_temp_pass)
        
        if valido and datos['rol'] == 'admin':
            st.success("✅ Autenticado como administrador")
            
            # Formulario de registro
            with st.form("registro_form"):
                st.markdown("### Crear nuevo usuario")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_user = st.text_input("Nuevo usuario")
                    new_pass = st.text_input("Nueva contraseña", type="password")
                    new_pass_confirm = st.text_input("Confirmar contraseña", type="password")
                
                with col2:
                    new_nombre = st.text_input("Nombre completo")
                    new_email = st.text_input("Email (opcional)")
                    new_role = st.selectbox("Rol", options=["entrenador", "visor", "admin"])
                
                if st.form_submit_button("✅ Crear usuario", type="primary"):
                    # Validaciones
                    if not all([new_user, new_pass, new_nombre]):
                        st.error("Complete todos los campos obligatorios")
                    elif new_pass != new_pass_confirm:
                        st.error("Las contraseñas no coinciden")
                    elif len(new_pass) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    else:
                        # Crear usuario
                        success, msg = crear_usuario(
                            new_user,
                            new_pass,
                            new_role,
                            new_nombre,
                            new_email
                        )
                        
                        if success:
                            st.success(f"✅ {msg}")
                            st.info(f"Usuario '{new_user}' creado con rol '{new_role}'")
                        else:
                            st.error(f"❌ {msg}")
        elif valido:
            st.error("❌ Solo administradores pueden crear usuarios")
        else:
            st.error("❌ Credenciales de administrador inválidas")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <small>El Once Pro - Sistema de Planificación Táctica | TFM 2024</small>
    </div>
    """,
    unsafe_allow_html=True
)