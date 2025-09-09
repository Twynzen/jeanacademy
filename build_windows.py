#!/usr/bin/env python3
"""
SCRIPT PARA CREAR EJECUTABLE WINDOWS (.exe)
Funciona desde cualquier sistema operativo
"""

import os
import sys
import subprocess
import shutil
import platform
from datetime import datetime

def print_step(message):
    """Imprime paso con formato"""
    print(f"\n🔨 {message}")
    print("=" * 60)

def check_requirements():
    """Verifica que todo esté listo"""
    print_step("VERIFICANDO REQUISITOS PARA WINDOWS")
    
    # Verificar Python
    python_version = sys.version_info
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Verificar archivos esenciales
    required_files = [
        "jean_ejecutable_terminal.py",
        "app/",
        "requirements.txt",
        "jeanacademy-da03c7c92e89.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file}")
    
    if missing_files:
        print(f"❌ Archivos faltantes: {missing_files}")
        print("💡 Asegúrate de tener todos los archivos del proyecto")
        return False
    
    return True

def install_dependencies():
    """Instala dependencias necesarias"""
    print_step("INSTALANDO DEPENDENCIAS")
    
    try:
        # Instalar requirements
        print("📦 Instalando dependencias del proyecto...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        
        # Instalar PyInstaller
        print("📦 Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                      check=True, capture_output=True)
        
        print("✅ Todas las dependencias instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def build_windows_executable():
    """Construye el ejecutable para Windows"""
    print_step("CONSTRUYENDO EJECUTABLE WINDOWS (.exe)")
    
    exe_name = "AcademiaJean"
    
    print(f"🎯 Target: Windows")
    print(f"📁 Nombre del ejecutable: {exe_name}.exe")
    
    # Limpiar builds anteriores
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Comando PyInstaller para Windows
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Un solo archivo
        "--windowed",          # Sin consola (GUI)
        "--name", exe_name,
        "--icon", "NONE",      # Sin icono por ahora
        "--add-data", f"app{os.pathsep}app",
        "--add-data", f"jeanacademy-da03c7c92e89.json{os.pathsep}.",
        "--hidden-import", "pandas",
        "--hidden-import", "xlsxwriter",
        "--hidden-import", "google.oauth2.service_account",
        "--hidden-import", "googleapiclient.discovery",
        "--hidden-import", "tkinter",
        "--distpath", "dist_windows",
        "--clean",             # Limpiar cache
        "--noconfirm",         # No pedir confirmación
        "jean_ejecutable_terminal.py"
    ]
    
    try:
        print("🔥 Ejecutando PyInstaller...")
        print("⏳ Esto puede tomar 2-5 minutos...")
        
        # Ejecutar con output visible
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Mostrar progreso
        for line in process.stdout:
            if "Building" in line or "Copying" in line or "WARNING" in line:
                print(f"   {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            print("✅ Ejecutable construido exitosamente!")
            return exe_name
        else:
            print("❌ Error en la construcción del ejecutable")
            return None
        
    except Exception as e:
        print(f"❌ Error construyendo ejecutable: {e}")
        return None

def create_windows_package(exe_name):
    """Crea paquete ZIP listo para Windows"""
    print_step("CREANDO PAQUETE PARA WINDOWS")
    
    # Crear carpeta de entrega
    delivery_folder = f"AcademiaJean_Windows_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(delivery_folder):
        shutil.rmtree(delivery_folder)
    
    os.makedirs(delivery_folder)
    print(f"📁 Carpeta de entrega: {delivery_folder}")
    
    # Copiar ejecutable
    exe_file = f"dist_windows/{exe_name}.exe"
    if os.path.exists(exe_file):
        shutil.copy(exe_file, f"{delivery_folder}/{exe_name}.exe")
        print(f"✅ Copiado: {exe_name}.exe")
    else:
        print(f"❌ No se encontró el ejecutable en {exe_file}")
        return None
    
    # Copiar credenciales (Jean las reemplazará con las suyas)
    if os.path.exists("jeanacademy-da03c7c92e89.json"):
        shutil.copy("jeanacademy-da03c7c92e89.json", delivery_folder)
        print("✅ Copiado: Credenciales Google (reemplazar con las de Jean)")
    
    # Crear instrucciones para Windows
    instructions = f"""🎨 ACADEMIA JEAN - SISTEMA DE REPORTES
=============================================
VERSIÓN WINDOWS

✅ INSTRUCCIONES DE USO:

1. EJECUTAR:
   - Doble-click en {exe_name}.exe
   - Si Windows bloquea, click en "Más información" → "Ejecutar de todos modos"

2. CONFIGURACIÓN INICIAL:
   - El programa solicitará el ID de la carpeta Google Drive
   - Pegar el ID de tu carpeta de módulos

3. USAR:
   - Botón 1: "Rastrear Google Drive" - Verifica conexión
   - Botón 2: "Generar Reporte Excel" - Crea el reporte

4. CREDENCIALES:
   ⚠️ IMPORTANTE: Reemplazar jeanacademy-da03c7c92e89.json con TUS credenciales
   - Obtener desde Google Cloud Console
   - Crear Service Account con permisos de lectura
   - Descargar JSON y reemplazar el archivo incluido

📊 CARACTERÍSTICAS:
   - Terminal integrada con logs en tiempo real
   - Genera reportes Excel profesionales
   - Sistema dinámico que se adapta a cualquier carpeta

📞 SOPORTE:
   Email: darmcastiblanco@gmail.com
   Proyecto: Academia Jean €250

📅 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ Sistema: Windows
"""
    
    with open(f"{delivery_folder}/INSTRUCCIONES_WINDOWS.txt", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("✅ Creado: INSTRUCCIONES_WINDOWS.txt")
    
    # Mostrar contenido final
    print(f"\n📦 CONTENIDO DEL PAQUETE:")
    for item in os.listdir(delivery_folder):
        path = os.path.join(delivery_folder, item)
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024*1024)
            print(f"   📄 {item} ({size_mb:.1f} MB)")
    
    return delivery_folder

def create_windows_zip(delivery_folder):
    """Crea ZIP final para Windows"""
    print_step("CREANDO ZIP PARA WINDOWS")
    
    zip_name = f"{delivery_folder}.zip"
    
    try:
        shutil.make_archive(delivery_folder, 'zip', delivery_folder)
        
        if os.path.exists(zip_name):
            size_mb = os.path.getsize(zip_name) / (1024*1024)
            print(f"✅ ZIP creado: {zip_name}")
            print(f"📏 Tamaño: {size_mb:.1f} MB")
            
            if size_mb < 25:
                print("✅ Perfecto para email directo (< 25MB)")
            elif size_mb < 100:
                print("⚠️ Usar Google Drive o WeTransfer para enviar")
            else:
                print("❌ Muy grande, considera optimizar")
            
            return zip_name
        else:
            print("❌ Error creando ZIP")
            return None
            
    except Exception as e:
        print(f"❌ Error creando ZIP: {e}")
        return None

def main():
    """Función principal"""
    print("🪟 CONSTRUIR EJECUTABLE WINDOWS PARA ACADEMIA JEAN")
    print("=" * 60)
    print(f"🖥️ Sistema actual: {platform.system()}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Paso 1: Verificar requisitos
    if not check_requirements():
        print("\n❌ Faltan archivos necesarios. Abortando.")
        return
    
    # Paso 2: Instalar dependencias
    if not install_dependencies():
        print("\n❌ Error instalando dependencias. Abortando.")
        return
    
    # Paso 3: Construir ejecutable Windows
    exe_name = build_windows_executable()
    if not exe_name:
        print("\n❌ Error construyendo ejecutable. Abortando.")
        return
    
    # Paso 4: Crear paquete de entrega
    delivery_folder = create_windows_package(exe_name)
    if not delivery_folder:
        print("\n❌ Error creando paquete. Abortando.")
        return
    
    # Paso 5: Crear ZIP
    zip_file = create_windows_zip(delivery_folder)
    
    # Resumen final
    print_step("🎉 CONSTRUCCIÓN COMPLETADA PARA WINDOWS")
    print(f"✅ Ejecutable Windows: {exe_name}.exe")
    print(f"✅ Carpeta de entrega: {delivery_folder}")
    if zip_file:
        print(f"✅ Archivo ZIP: {zip_file}")
        print(f"\n📧 LISTO PARA ENVIAR A JEAN:")
        print(f"   Adjuntar: {zip_file}")
        print(f"   Asunto: 'Academia Jean - Sistema de Reportes Windows €250'")
    
    print(f"\n💡 NOTAS IMPORTANTES:")
    print(f"   1. Este ejecutable funciona en Windows 7/8/10/11")
    print(f"   2. Jean debe reemplazar las credenciales con las suyas")
    print(f"   3. El sistema se adapta dinámicamente a cualquier carpeta")
    print(f"\n🚀 ¡Ejecutable Windows listo para Jean!")

if __name__ == "__main__":
    main()