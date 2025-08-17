# clean_cache.ps1
# 🧹 Script de limpieza de cachés Python para el proyecto de planificación táctica

Write-Host "🧹 Iniciando limpieza de archivos .pyc y carpetas __pycache__..." -ForegroundColor Cyan

# Buscar y eliminar archivos .pyc y carpetas __pycache__
Get-ChildItem -Path . -Recurse -Include *.pyc, *__pycache__* | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

Write-Host "✅ Limpieza completada correctamente." -ForegroundColor Green
