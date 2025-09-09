#!/usr/bin/env python3
"""
SCRIPT PARA CONSTRUIR EJECUTABLE PARA JEAN
Ejecutar en cualquier PC para crear el .exe/.app listo para enviar
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
    print_step("VERIFICANDO REQUISITOS")
    
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
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # Instalar PyInstaller
        print("📦 Instalando PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
        print("✅ Todas las dependencias instaladas")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def build_executable():
    """Construye el ejecutable"""
    print_step("CONSTRUYENDO EJECUTABLE")
    
    # Determinar configuración según OS
    system = platform.system()
    if system == "Windows":
        exe_name = "AcademiaJean_Windows"
        windowed_flag = "--windowed"
    elif system == "Darwin":  # macOS
        exe_name = "AcademiaJean_macOS"
        windowed_flag = "--windowed"
    else:  # Linux
        exe_name = "AcademiaJean_Linux"
        windowed_flag = "--console"  # En Linux mejor con consola
    
    print(f"🖥️ Sistema detectado: {system}")
    print(f"📁 Nombre del ejecutable: {exe_name}")
    
    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        windowed_flag,
        "--name", exe_name,
        "--add-data", f"app{os.pathsep}app",
        "--add-data", f"jeanacademy-da03c7c92e89.json{os.pathsep}.",
        "--hidden-import", "pandas",
        "--hidden-import", "xlsxwriter",
        "--hidden-import", "google.oauth2.service_account",
        "--hidden-import", "googleapiclient.discovery",
        "--distpath", "jean_executables",
        "jean_ejecutable_terminal.py"
    ]
    
    try:
        print("🔥 Ejecutando PyInstaller...")
        print("⏳ Esto puede tomar varios minutos...")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Ejecutable construido exitosamente!")
        return exe_name
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error construyendo ejecutable:")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return None

def create_delivery_package(exe_name):
    """Crea paquete listo para enviar a Jean"""
    print_step("CREANDO PAQUETE DE ENTREGA")
    
    # Crear carpeta de entrega
    delivery_folder = f"academia_jean_entrega_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(delivery_folder):
        shutil.rmtree(delivery_folder)
    
    os.makedirs(delivery_folder)
    print(f"📁 Carpeta de entrega: {delivery_folder}")
    
    # Copiar ejecutable
    system = platform.system()
    if system == "Darwin" and os.path.exists(f"jean_executables/{exe_name}.app"):
        # macOS - copiar .app
        shutil.copytree(f"jean_executables/{exe_name}.app", f"{delivery_folder}/{exe_name}.app")
        print(f"✅ Copiado: {exe_name}.app")
    else:
        # Windows/Linux - copiar ejecutable directo
        exe_extension = ".exe" if system == "Windows" else ""
        exe_file = f"jean_executables/{exe_name}{exe_extension}"
        if os.path.exists(exe_file):
            shutil.copy(exe_file, f"{delivery_folder}/{exe_name}{exe_extension}")
            print(f"✅ Copiado: {exe_name}{exe_extension}")
    
    # Copiar credenciales
    if os.path.exists("jeanacademy-da03c7c92e89.json"):
        shutil.copy("jeanacademy-da03c7c92e89.json", delivery_folder)
        print("✅ Copiado: Credenciales Google")
    
    # Crear instrucciones simples
    instructions = f"""🎨 ACADEMIA JEAN - SISTEMA DE REPORTES
=============================================

✅ INSTRUCCIONES DE USO:

1. EJECUTAR:
   - Doble-click en el archivo ejecutable
   - Sistema: {system}

2. USAR:
   - Botón 1: "Rastrear Google Drive"
   - Botón 2: "Generar Reporte Excel"

3. ¡LISTO!
   - El Excel se genera automáticamente
   - Contiene todas las estadísticas de entregas

📞 SOPORTE:
   Email: darmcastiblanco@gmail.com
   Proyecto: Academia Jean €250

📅 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ Sistema: {system}
"""
    
    with open(f"{delivery_folder}/INSTRUCCIONES.txt", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    print("✅ Copiado: INSTRUCCIONES.txt")
    
    # Mostrar contenido final
    print(f"\n📦 CONTENIDO DEL PAQUETE:")
    for item in os.listdir(delivery_folder):
        path = os.path.join(delivery_folder, item)
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024*1024)
            print(f"   📄 {item} ({size_mb:.1f} MB)")
        else:
            print(f"   📁 {item}/")
    
    return delivery_folder

def create_zip_package(delivery_folder):
    """Crea ZIP para enviar por email"""
    print_step("CREANDO ARCHIVO ZIP")
    
    zip_name = f"{delivery_folder}.zip"
    
    try:
        shutil.make_archive(delivery_folder, 'zip', delivery_folder)
        
        if os.path.exists(zip_name):
            size_mb = os.path.getsize(zip_name) / (1024*1024)
            print(f"✅ ZIP creado: {zip_name}")
            print(f"📏 Tamaño: {size_mb:.1f} MB")
            
            if size_mb < 25:
                print("✅ Perfecto para email directo (< 25MB)")
            elif size_mb < 50:
                print("⚠️ Usar Google Drive o WeTransfer (> 25MB)")
            else:
                print("❌ Demasiado grande para email normal")
            
            return zip_name
        else:
            print("❌ Error creando ZIP")
            return None
            
    except Exception as e:
        print(f"❌ Error creando ZIP: {e}")
        return None

def main():
    """Función principal"""
    print("🎨 CONSTRUIR EJECUTABLE PARA ACADEMIA JEAN")
    print("=" * 60)
    print(f"🖥️ Sistema: {platform.system()}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Paso 1: Verificar requisitos
    if not check_requirements():
        print("❌ Faltan archivos necesarios. Abortando.")
        return
    
    # Paso 2: Instalar dependencias
    if not install_dependencies():
        print("❌ Error instalando dependencias. Abortando.")
        return
    
    # Paso 3: Construir ejecutable
    exe_name = build_executable()
    if not exe_name:
        print("❌ Error construyendo ejecutable. Abortando.")
        return
    
    # Paso 4: Crear paquete de entrega
    delivery_folder = create_delivery_package(exe_name)
    if not delivery_folder:
        print("❌ Error creando paquete. Abortando.")
        return
    
    # Paso 5: Crear ZIP
    zip_file = create_zip_package(delivery_folder)
    
    # Resumen final
    print_step("🎉 CONSTRUCCIÓN COMPLETADA")
    print(f"✅ Ejecutable listo: {exe_name}")
    print(f"✅ Carpeta de entrega: {delivery_folder}")
    if zip_file:
        print(f"✅ Archivo ZIP: {zip_file}")
        print(f"\n📧 LISTO PARA ENVIAR A JEAN:")
        print(f"   Adjuntar: {zip_file}")
        print(f"   Asunto: 'Academia Jean - Sistema de Reportes €250'")
    
    print(f"\n💡 PRÓXIMOS PASOS:")
    print(f"   1. Probar el ejecutable localmente")
    print(f"   2. Enviar ZIP por email a Jean")
    print(f"   3. ¡Disfrutar del pago! 💰")

if __name__ == "__main__":
    main()