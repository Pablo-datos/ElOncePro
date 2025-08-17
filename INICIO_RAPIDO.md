# 🚀 Guía de Inicio Rápido - El Once Pro

## Paso 1: Preparar el entorno

```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Instalar dependencias
pip install -r requirements.txt
```

## Paso 2: Iniciar la aplicación

```bash
streamlit run app.py
```

## Paso 3: Iniciar sesión

1. Abre tu navegador en `http://localhost:8501`
2. Usa las credenciales:
   - Usuario: `admin`
   - Contraseña: `admin123`

## Paso 4: Navegar por los módulos

### Sistema de navegación:
El sistema cuenta con un **menú de navegación personalizado** en el sidebar que permite acceso rápido a todas las páginas. La navegación automática de Streamlit está deshabilitada para una experiencia más limpia.

### Módulos principales:

#### 📊 **Dashboard**
- Vista general del sistema
- Métricas y estadísticas
- Accesos rápidos

#### 📋 **Planificación Táctica**
- Crear y editar microciclos
- Asignar principios tácticos por día y bloque
- Gestionar cuerpo técnico

#### 🤖 **Predicción Táctica**
- Entrenar modelo ML con datos históricos
- Obtener sugerencias de principios
- Análisis de similitud entre microciclos

#### 👁️ **Vista Planificación**
- Visualizar planificaciones guardadas
- Filtrar por temporada/categoría/microciclo
- Exportar a Excel/PDF (según permisos)

## 📝 Flujo de trabajo típico

1. **Configurar temporada y categorías** en Planificación
2. **Crear microciclos** con fechas específicas
3. **Asignar principios tácticos** por día y bloque
4. **Entrenar el modelo ML** con datos acumulados
5. **Obtener predicciones** para nuevos microciclos
6. **Exportar planificaciones** para compartir con el equipo

## ⚠️ Notas importantes

- El sistema crea backups automáticos antes de cambios importantes
- Solo administradores pueden eliminar datos
- Los visores tienen acceso de solo lectura
- El modelo ML necesita al menos 10 combinaciones únicas para entrenarse

## 🆘 Solución de problemas

**La app no inicia:**
- Verifica que el entorno virtual esté activado
- Reinstala las dependencias: `pip install -r requirements.txt`

**Error de módulos faltantes:**
```bash
pip install streamlit pandas plotly scikit-learn joblib bcrypt fpdf2 openpyxl
```

**No puedo ver algunas páginas:**
- Verifica tu rol de usuario
- Algunos módulos requieren permisos de admin o entrenador

---

*El Once Pro - EL ONCE Fútbol*