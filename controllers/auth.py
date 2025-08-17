# controllers/auth.py

import pandas as pd
import bcrypt
import os
import streamlit as st
from datetime import datetime
import shutil

# Configuración
USUARIOS_CSV = "data/usuarios.csv"
COLUMNAS_REQUERIDAS = ["usuario", "password", "rol"]
COLUMNAS_COMPLETAS = ["usuario", "password", "rol", "nombre_completo", "email", "fecha_creacion", "activo"]

# Usuario admin por defecto
ADMIN_DEFAULT = {
    "usuario": "admin",
    "password_plain": "admin123",  # Solo para referencia, nunca se guarda
    "rol": "admin",
    "nombre_completo": "Administrador",
    "email": "admin@sistema.com",
    "activo": True
}

def crear_backup_usuarios():
    """Crea un backup del archivo de usuarios antes de modificarlo"""
    if os.path.exists(USUARIOS_CSV):
        backup_dir = "data/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"usuarios_{timestamp}.bak")
        
        try:
            shutil.copy2(USUARIOS_CSV, backup_path)
            return backup_path
        except:
            pass
    return None

def validar_estructura_csv():
    """
    Valida que el archivo CSV existe y tiene la estructura correcta.
    Retorna: (es_valido, mensaje_error)
    """
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(USUARIOS_CSV), exist_ok=True)
    
    # Verificar si el archivo existe
    if not os.path.exists(USUARIOS_CSV):
        return False, "El archivo no existe"
    
    try:
        # Intentar leer el archivo
        df = pd.read_csv(USUARIOS_CSV)
        
        # Verificar si está vacío
        if df.empty:
            return False, "El archivo está vacío"
        
        # Verificar columnas requeridas
        columnas_faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
        if columnas_faltantes:
            return False, f"Faltan columnas requeridas: {', '.join(columnas_faltantes)}"
        
        # Verificar que hay al menos un registro
        if len(df) == 0:
            return False, "No hay usuarios en el archivo"
        
        return True, "Estructura válida"
        
    except pd.errors.EmptyDataError:
        return False, "El archivo está vacío o corrupto"
    except Exception as e:
        return False, f"Error al leer el archivo: {str(e)}"

def inicializar_sistema_usuarios():
    """
    Inicializa el sistema de usuarios creando el archivo con estructura correcta
    y usuario admin por defecto si es necesario.
    """
    es_valido, mensaje = validar_estructura_csv()
    
    if not es_valido:
        print(f"⚠️ Sistema de usuarios no válido: {mensaje}")
        print("🔧 Inicializando sistema de usuarios...")
        
        # Crear backup si existe archivo corrupto
        if os.path.exists(USUARIOS_CSV):
            backup = crear_backup_usuarios()
            if backup:
                print(f"📦 Backup creado: {backup}")
        
        # Crear estructura completa
        df_nuevo = pd.DataFrame(columns=COLUMNAS_COMPLETAS)
        
        # Crear usuario admin por defecto
        password_hash = bcrypt.hashpw(
            ADMIN_DEFAULT["password_plain"].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        admin_registro = {
            "usuario": ADMIN_DEFAULT["usuario"],
            "password": password_hash,
            "rol": ADMIN_DEFAULT["rol"],
            "nombre_completo": ADMIN_DEFAULT["nombre_completo"],
            "email": ADMIN_DEFAULT["email"],
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }
        
        df_nuevo = pd.concat([df_nuevo, pd.DataFrame([admin_registro])], ignore_index=True)
        
        # Guardar archivo
        df_nuevo.to_csv(USUARIOS_CSV, index=False)
        print("✅ Sistema de usuarios inicializado correctamente")
        print("👤 Usuario admin creado: admin / admin123")
        
        return True
    else:
        # Verificar si existe usuario admin
        df = pd.read_csv(USUARIOS_CSV)
        if not any(df['usuario'] == 'admin'):
            print("⚠️ No se encontró usuario admin, creando...")
            crear_usuario_admin_si_no_existe()
        
        return True

def crear_usuario_admin_si_no_existe():
    """Crea el usuario admin si no existe en el sistema"""
    try:
        df = pd.read_csv(USUARIOS_CSV)
        
        # Verificar si ya existe
        if any(df['usuario'] == 'admin'):
            return False, "El usuario admin ya existe"
        
        # Crear hash de password
        password_hash = bcrypt.hashpw(
            ADMIN_DEFAULT["password_plain"].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Crear registro completo
        nuevo_admin = {
            "usuario": ADMIN_DEFAULT["usuario"],
            "password": password_hash,
            "rol": ADMIN_DEFAULT["rol"],
            "nombre_completo": ADMIN_DEFAULT.get("nombre_completo", "Administrador"),
            "email": ADMIN_DEFAULT.get("email", ""),
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }
        
        # Añadir columnas faltantes si es necesario
        for col in COLUMNAS_COMPLETAS:
            if col not in df.columns:
                df[col] = ""
        
        # Añadir el nuevo usuario
        df = pd.concat([df, pd.DataFrame([nuevo_admin])], ignore_index=True)
        
        # Guardar
        df.to_csv(USUARIOS_CSV, index=False)
        
        return True, "Usuario admin creado correctamente"
        
    except Exception as e:
        return False, f"Error al crear usuario admin: {str(e)}"

def validar_credenciales(usuario, password):
    """
    Valida las credenciales del usuario.
    Retorna: (es_valido, mensaje, datos_usuario)
    """
    # Inicializar sistema si es necesario
    inicializar_sistema_usuarios()
    
    try:
        # Leer usuarios
        df = pd.read_csv(USUARIOS_CSV)
        
        # Buscar usuario (case insensitive)
        usuario_lower = usuario.lower()
        df_usuario = df[df['usuario'].str.lower() == usuario_lower]
        
        if df_usuario.empty:
            return False, "Usuario no encontrado", None
        
        # Obtener datos del usuario
        usuario_data = df_usuario.iloc[0]
        
        # Verificar si está activo
        if 'activo' in df.columns and not usuario_data.get('activo', True):
            return False, "Usuario desactivado", None
        
        # Verificar password
        password_hash = usuario_data['password']
        
        # Manejar diferentes formatos de hash
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            # Login exitoso
            datos_usuario = {
                "usuario": usuario_data['usuario'],
                "rol": usuario_data['rol'],
                "nombre_completo": usuario_data.get('nombre_completo', usuario_data['usuario']),
                "email": usuario_data.get('email', '')
            }
            return True, "Login exitoso", datos_usuario
        else:
            return False, "Contraseña incorrecta", None
            
    except Exception as e:
        return False, f"Error al validar: {str(e)}", None

def crear_usuario(usuario, password, rol, nombre_completo="", email=""):
    """
    Crea un nuevo usuario en el sistema.
    Retorna: (exitoso, mensaje)
    """
    # Inicializar sistema si es necesario
    inicializar_sistema_usuarios()
    
    try:
        # Leer usuarios existentes
        df = pd.read_csv(USUARIOS_CSV)
        
        # Verificar si el usuario ya existe
        if any(df['usuario'].str.lower() == usuario.lower()):
            return False, "El usuario ya existe"
        
        # Crear hash de password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Crear nuevo registro
        nuevo_usuario = {
            "usuario": usuario,
            "password": password_hash,
            "rol": rol,
            "nombre_completo": nombre_completo or usuario,
            "email": email,
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }
        
        # Asegurar que todas las columnas existen
        for col in COLUMNAS_COMPLETAS:
            if col not in df.columns:
                df[col] = ""
        
        # Añadir nuevo usuario
        df = pd.concat([df, pd.DataFrame([nuevo_usuario])], ignore_index=True)
        
        # Eliminar duplicados por si acaso (basándose en el campo usuario)
        df = df.drop_duplicates(subset=['usuario'], keep='last')
        
        # Guardar
        crear_backup_usuarios()  # Backup antes de guardar
        df.to_csv(USUARIOS_CSV, index=False)
        
        return True, "Usuario creado correctamente"
        
    except Exception as e:
        return False, f"Error al crear usuario: {str(e)}"

def cambiar_password(usuario, password_actual, password_nueva):
    """
    Cambia la contraseña de un usuario.
    Retorna: (exitoso, mensaje)
    """
    # Primero validar credenciales actuales
    valido, mensaje, _ = validar_credenciales(usuario, password_actual)
    
    if not valido:
        return False, "Contraseña actual incorrecta"
    
    try:
        # Leer usuarios
        df = pd.read_csv(USUARIOS_CSV)
        
        # Buscar usuario
        mask = df['usuario'].str.lower() == usuario.lower()
        
        if not any(mask):
            return False, "Usuario no encontrado"
        
        # Crear nuevo hash
        password_hash = bcrypt.hashpw(
            password_nueva.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Actualizar password
        df.loc[mask, 'password'] = password_hash
        
        # Guardar
        crear_backup_usuarios()
        df.to_csv(USUARIOS_CSV, index=False)
        
        return True, "Contraseña actualizada correctamente"
        
    except Exception as e:
        return False, f"Error al cambiar contraseña: {str(e)}"

def listar_usuarios():
    """
    Lista todos los usuarios del sistema.
    Retorna: DataFrame con usuarios (sin passwords)
    """
    try:
        df = pd.read_csv(USUARIOS_CSV)
        
        # Remover columna de password por seguridad
        columnas_mostrar = [col for col in df.columns if col != 'password']
        
        return df[columnas_mostrar]
        
    except Exception:
        return pd.DataFrame()

def eliminar_usuario(usuario):
    """
    Elimina un usuario del sistema (excepto admin).
    Retorna: (exitoso, mensaje)
    """
    if usuario.lower() == 'admin':
        return False, "No se puede eliminar el usuario admin"
    
    try:
        df = pd.read_csv(USUARIOS_CSV)
        
        # Crear backup antes de eliminar
        crear_backup_usuarios()
        
        # Filtrar usuario
        df_filtrado = df[df['usuario'].str.lower() != usuario.lower()]
        
        if len(df_filtrado) == len(df):
            return False, "Usuario no encontrado"
        
        # Guardar
        df_filtrado.to_csv(USUARIOS_CSV, index=False)
        
        return True, "Usuario eliminado correctamente"
        
    except Exception as e:
        return False, f"Error al eliminar usuario: {str(e)}"

# Función para mostrar formulario de login en Streamlit
def mostrar_login():
    """Muestra el formulario de login en Streamlit"""
    st.markdown("### 🔐 Inicio de Sesión")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuario", key="login_usuario")
        password = st.text_input("Contraseña", type="password", key="login_password")
        submit = st.form_submit_button("Iniciar Sesión", type="primary")
        
        if submit:
            if not usuario or not password:
                st.error("Por favor complete todos los campos")
            else:
                valido, mensaje, datos_usuario = validar_credenciales(usuario, password)
                
                if valido:
                    st.session_state.authenticated = True
                    st.session_state.usuario = datos_usuario['usuario']
                    st.session_state.rol = datos_usuario['rol']
                    st.session_state.nombre_completo = datos_usuario['nombre_completo']
                    st.success(f"¡Bienvenido {datos_usuario['nombre_completo']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {mensaje}")
    
    # Información adicional
    with st.expander("ℹ️ Información de acceso"):
        st.info("""
        **Usuario por defecto:**
        - Usuario: `admin`
        - Contraseña: `admin123`
        
        **Roles disponibles:**
        - `admin`: Acceso completo
        - `entrenador`: Acceso a planificación
        - `visor`: Solo lectura
        """)

# Inicializar sistema al importar el módulo
if __name__ != "__main__":
    inicializar_sistema_usuarios()