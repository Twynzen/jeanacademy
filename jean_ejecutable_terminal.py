#!/usr/bin/env python3
"""
APLICACIÓN FINAL PARA JEAN - VERSIÓN CON TERMINAL INTEGRADA
Interfaz completa con logs en tiempo real
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from datetime import datetime
import threading
import pandas as pd
import subprocess
import time

# Agregar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class AcademiaJeanAppTerminal:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎨 Academia Jean - Sistema de Reportes")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Variables
        self.config = self.load_config()
        self.setup_environment()
        
        # Crear interfaz
        self.create_interface()
        
        # Centrar ventana
        self.center_window()
        
        # Log inicial
        self.log("🚀 Sistema iniciado correctamente")
        self.log(f"👋 Bienvenido, {self.config['user_name']}")
        self.log(f"📂 Carpeta configurada: {self.config['drive_folder_id'][:30]}...")
    
    def load_config(self):
        """Carga configuración con valores por defecto"""
        config_file = 'jean_config.json'
        default_config = {
            "drive_folder_id": "1jfaCkTzYh-rsvy2efmLjPjuIMEDGQ7Jv",
            "google_credentials_file": "jeanacademy-da03c7c92e89.json",
            "configured": True,
            "user_name": "Jean Fraisse",
            "academy_name": "École Jean Fraisse"
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except:
                pass
        
        return default_config
    
    def save_config(self):
        """Guarda configuración"""
        try:
            with open('jean_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"❌ Error guardando configuración: {e}")
    
    def setup_environment(self):
        """Configura variables de entorno"""
        os.environ['GOOGLE_SERVICE_ACCOUNT_JSON_PATH'] = self.config['google_credentials_file']
        os.environ['DRIVE_FOLDER_ID'] = self.config['drive_folder_id']
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def log(self, message):
        """Agregar mensaje a la terminal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\\n"
        
        # Agregar al final y hacer scroll automático
        self.terminal.insert(tk.END, log_line)
        self.terminal.see(tk.END)
        
        # Actualizar interfaz
        self.root.update_idletasks()
    
    def clear_terminal(self):
        """Limpiar terminal"""
        self.terminal.delete(1.0, tk.END)
        self.log("🧹 Terminal limpiada")
    
    def create_interface(self):
        """Crea la interfaz completa"""
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== PANEL SUPERIOR - CONTROLES ==========
        control_frame = ttk.Frame(main_frame)
        main_frame.add(control_frame, weight=1)
        
        # Título
        title_frame = ttk.Frame(control_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="🎨 Academia Jean - Sistema de Reportes",
            font=("Arial", 16, "bold"),
            fg="#1E3A8A"
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Rastrea Google Drive y genera reportes Excel automáticamente",
            font=("Arial", 9),
            fg="#666666"
        )
        subtitle_label.pack()
        
        # Frame de configuración
        config_frame = ttk.LabelFrame(control_frame, text="📁 Configuración de Carpeta Google Drive", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # ID de carpeta
        id_frame = ttk.Frame(config_frame)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(id_frame, text="ID Actual:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        self.drive_id_var = tk.StringVar(value=self.config["drive_folder_id"][:40] + "...")
        id_label = ttk.Label(id_frame, textvariable=self.drive_id_var, font=("Arial", 8), foreground="#10B981")
        id_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Botones de configuración
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X)
        
        change_btn = tk.Button(
            button_frame,
            text="📝 Cambiar Carpeta",
            command=self.change_drive_folder,
            bg="#3B82F6",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT
        )
        change_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        help_btn = tk.Button(
            button_frame,
            text="❓ Ayuda",
            command=self.show_help,
            bg="#F3F4F6",
            font=("Arial", 9),
            relief=tk.FLAT
        )
        help_btn.pack(side=tk.LEFT)
        
        # Frame de acciones principales
        actions_frame = ttk.LabelFrame(control_frame, text="🚀 Acciones Principales", padding="10")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Grid de botones principales
        buttons_grid = ttk.Frame(actions_frame)
        buttons_grid.pack(fill=tk.X)
        
        # Botón 1: Rastrear
        self.scan_button = tk.Button(
            buttons_grid,
            text="🔍 1. RASTREAR GOOGLE DRIVE",
            command=self.scan_drive_threaded,
            bg="#10B981",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            relief=tk.FLAT
        )
        self.scan_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 10))
        
        # Botón 2: Generar reporte
        self.report_button = tk.Button(
            buttons_grid,
            text="📊 2. GENERAR REPORTE EXCEL",
            command=self.generate_report_threaded,
            bg="#1E3A8A",
            fg="white",
            font=("Arial", 11, "bold"),
            height=2,
            relief=tk.FLAT
        )
        self.report_button.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 10))
        
        # Configurar grid
        buttons_grid.columnconfigure(0, weight=1)
        buttons_grid.columnconfigure(1, weight=1)
        
        # Botón limpiar terminal
        clear_btn = tk.Button(
            buttons_grid,
            text="🧹 Limpiar Terminal",
            command=self.clear_terminal,
            bg="#6B7280",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT
        )
        clear_btn.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        # ========== PANEL INFERIOR - TERMINAL ==========
        terminal_frame = ttk.LabelFrame(main_frame, text="📟 Terminal - Progreso en Tiempo Real", padding="5")
        main_frame.add(terminal_frame, weight=1)
        
        # Terminal con scroll
        self.terminal = scrolledtext.ScrolledText(
            terminal_frame,
            height=15,
            font=("Courier New", 9),
            bg="#1a1a1a",
            fg="#00ff00",
            insertbackground="#00ff00",
            wrap=tk.WORD
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)
        
        # Frame de estado
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X)
        
        # Estado de credenciales
        cred_status = "✅ Credenciales OK" if os.path.exists(self.config['google_credentials_file']) else "⚠️ Verificar credenciales"
        self.status_label = tk.Label(
            status_frame,
            text=f"Estado: {cred_status} | Usuario: {self.config['user_name']}",
            font=("Arial", 8),
            fg="#666666"
        )
        self.status_label.pack()
    
    def change_drive_folder(self):
        """Permite cambiar el ID de la carpeta"""
        self.log("⚙️ Abriendo diálogo para cambiar carpeta...")
        
        dialog_text = """Ingresa el ID de tu carpeta Google Drive:

💡 Para obtenerlo:
1. Abre la carpeta en Google Drive
2. Copia la URL completa
3. El ID es la parte después de '/folders/'

Ejemplo:
URL: https://drive.google.com/drive/folders/1ABC123XYZ
ID:  1ABC123XYZ"""
        
        new_id = simpledialog.askstring(
            "Cambiar Carpeta Google Drive",
            dialog_text,
            initialvalue=self.config['drive_folder_id']
        )
        
        if new_id and new_id.strip():
            old_id = self.config['drive_folder_id'][:30]
            self.config['drive_folder_id'] = new_id.strip()
            self.drive_id_var.set(new_id.strip()[:40] + "...")
            self.setup_environment()
            self.save_config()
            
            self.log(f"✅ Carpeta actualizada:")
            self.log(f"   Anterior: {old_id}...")
            self.log(f"   Nueva: {new_id.strip()[:30]}...")
            self.log("💾 Configuración guardada")
            
            messagebox.showinfo("Éxito", "¡Carpeta actualizada correctamente!")
        else:
            self.log("❌ Cambio de carpeta cancelado")
    
    def show_help(self):
        """Muestra ayuda detallada"""
        self.log("📚 Mostrando ayuda para obtener ID de carpeta...")
        
        help_text = """🔍 GUÍA COMPLETA - OBTENER ID DE CARPETA GOOGLE DRIVE

📋 PASOS DETALLADOS:
1️⃣ Abre Google Drive en tu navegador web
2️⃣ Navega hasta la carpeta que contiene tus módulos
3️⃣ Haz clic en la carpeta para entrar
4️⃣ Copia la URL completa de la barra de direcciones
5️⃣ El ID es la parte después de '/folders/'

📖 EJEMPLO PRÁCTICO:
URL completa: 
https://drive.google.com/drive/folders/1jfaCkTzYh-rsvy2efmLjPjuIMEDGQ7Jv

ID de la carpeta: 
1jfaCkTzYh-rsvy2efmLjPjuIMEDGQ7Jv

⚠️ REQUISITOS IMPORTANTES:
• La carpeta debe contener las subcarpetas de módulos
• El sistema tiene permisos de solo lectura
• Funciona con carpetas compartidas

🎯 ESTRUCTURA ESPERADA:
Tu Carpeta/
├── Módulo 1/
├── Módulo 2/
├── Módulo 3/
└── etc..."""
        
        messagebox.showinfo("Ayuda - ID de Carpeta Google Drive", help_text)
    
    def scan_drive_threaded(self):
        """Inicia rastreo en hilo separado"""
        self.scan_button.config(state=tk.DISABLED, text="🔄 RASTREANDO...")
        self.log("🔍 Iniciando rastreo de Google Drive...")
        threading.Thread(target=self.scan_drive, daemon=True).start()
    
    def scan_drive(self):
        """Escanea Google Drive con logs detallados"""
        try:
            self.log("📂 Importando cliente de Google Drive...")
            from app.ingest.drive_client import GoogleDriveClient
            
            self.log("🔐 Autenticando con Google Drive...")
            client = GoogleDriveClient()
            
            self.log("📁 Obteniendo lista de módulos...")
            modules = client.list_folders_in_root()
            
            self.log(f"✅ Rastreo completado exitosamente!")
            self.log(f"📊 RESULTADOS:")
            self.log(f"   • Módulos detectados: {len(modules)}")
            self.log(f"   • Conexión: ✅ Funcionando perfectamente")
            self.log(f"   • Estado: Listo para generar reportes")
            
            # Mostrar algunos módulos como ejemplo
            self.log(f"📋 Primeros módulos encontrados:")
            for i, module in enumerate(modules[:5], 1):
                self.log(f"   {i}. 📁 {module['name']}")
            
            if len(modules) > 5:
                self.log(f"   ... y {len(modules) - 5} módulos más")
            
            # Actualizar interfaz en hilo principal
            self.root.after(0, lambda: self.scan_completed(len(modules)))
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ ERROR durante el rastreo:")
            self.log(f"   {error_msg[:100]}...")
            self.root.after(0, lambda: self.scan_error(error_msg))
    
    def scan_completed(self, module_count):
        """Callback cuando el rastreo termina"""
        self.scan_button.config(state=tk.NORMAL, text="🔍 1. RASTREAR GOOGLE DRIVE")
        
        messagebox.showinfo(
            "🎉 Rastreo Completado",
            f"✅ RASTREO EXITOSO\\n\\n"
            f"📊 Resultados:\\n"
            f"• {module_count} módulos detectados\\n"
            f"• Conexión: ✅ Funcionando\\n"
            f"• Sistema: ✅ Listo\\n\\n"
            f"🎯 Ahora puedes generar tu reporte Excel"
        )
    
    def scan_error(self, error):
        """Callback cuando hay error en rastreo"""
        self.scan_button.config(state=tk.NORMAL, text="🔍 1. RASTREAR GOOGLE DRIVE")
        
        messagebox.showerror(
            "❌ Error de Conexión",
            f"No se pudo conectar a Google Drive:\\n\\n"
            f"Error: {error[:150]}...\\n\\n"
            f"💡 Soluciones:\\n"
            f"• Verifica tu conexión a internet\\n"
            f"• Confirma que el ID de carpeta sea correcto\\n"
            f"• Intenta cambiar la carpeta si es necesario"
        )
    
    def generate_report_threaded(self):
        """Inicia generación de reporte en hilo separado"""
        self.report_button.config(state=tk.DISABLED, text="📊 GENERANDO...")
        self.log("📊 Iniciando generación de reporte Excel...")
        threading.Thread(target=self.generate_report, daemon=True).start()
    
    def generate_report(self):
        """Genera reporte con logs detallados"""
        try:
            self.log("📂 Importando cliente de Google Drive...")
            from app.ingest.drive_client import GoogleDriveClient
            
            self.log("🔐 Conectando a Google Drive...")
            client = GoogleDriveClient()
            
            self.log("📁 Obteniendo lista de módulos...")
            modules = client.list_folders_in_root()
            self.log(f"   ✅ {len(modules)} módulos encontrados")
            
            self.log("🔍 Analizando archivos en cada módulo...")
            
            # Procesar módulos
            datos_entregas = []
            total_archivos = 0
            estudiantes_unicos = set()
            
            for i, module in enumerate(modules, 1):
                self.log(f"   📁 {i}/{len(modules)} - Procesando: {module['name']}")
                
                try:
                    files = client.list_files_in_folder(module['id'])
                    archivos_img = [f for f in files if f['name'].lower().endswith(('.jpg', '.jpeg', '.png'))]
                    
                    # Detectar estudiantes
                    estudiantes_modulo = set()
                    for file in files:
                        # Por metadata
                        if file.get('lastModifyingUser', {}).get('displayName'):
                            nombre = file['lastModifyingUser']['displayName']
                            estudiantes_modulo.add(nombre)
                            estudiantes_unicos.add(nombre)
                        
                        # Por nombre de archivo
                        nombre_archivo = file['name']
                        if '_' in nombre_archivo:
                            partes = nombre_archivo.split('_')
                            if len(partes) >= 2:
                                posible_nombre = partes[1].replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
                                if len(posible_nombre) > 2 and not posible_nombre.isdigit():
                                    estudiantes_modulo.add(posible_nombre)
                                    estudiantes_unicos.add(posible_nombre)
                    
                    self.log(f"      📊 {len(files)} archivos, {len(estudiantes_modulo)} estudiantes")
                    
                    datos_entregas.append({
                        'Módulo': module['name'],
                        'Total Archivos': len(files),
                        'Archivos de Imagen': len(archivos_img),
                        'Estudiantes': len(estudiantes_modulo),
                        'Lista Estudiantes': ', '.join(list(estudiantes_modulo)[:3]) + ('...' if len(estudiantes_modulo) > 3 else ''),
                        'Última Actividad': files[0]['modifiedTime'][:10] if files else 'Sin archivos',
                        'Estado': '✅ Con entregas' if len(files) > 0 else '⚠️ Sin entregas'
                    })
                    
                    total_archivos += len(files)
                    
                except Exception as e:
                    self.log(f"      ⚠️ Error procesando módulo: {str(e)[:50]}...")
                    datos_entregas.append({
                        'Módulo': module['name'],
                        'Total Archivos': 0,
                        'Archivos de Imagen': 0,
                        'Estudiantes': 0,
                        'Lista Estudiantes': 'Error de acceso',
                        'Última Actividad': 'Error',
                        'Estado': '❌ Error'
                    })
                
                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.1)
            
            self.log("📄 Creando archivo Excel...")
            
            # Crear Excel
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_academia_jean_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                # Hoja principal
                df = pd.DataFrame(datos_entregas)
                df.to_excel(writer, sheet_name='Reporte de Entregas', index=False)
                self.log("   ✅ Hoja 'Reporte de Entregas' creada")
                
                # Hoja resumen
                modulos_activos = len([d for d in datos_entregas if d['Total Archivos'] > 0])
                resumen = pd.DataFrame([
                    {'Información': 'Academia', 'Valor': self.config['academy_name']},
                    {'Información': 'Generado por', 'Valor': self.config['user_name']},
                    {'Información': 'Fecha', 'Valor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
                    {'Información': 'Total Módulos', 'Valor': len(datos_entregas)},
                    {'Información': 'Módulos Activos', 'Valor': modulos_activos},
                    {'Información': 'Total Archivos', 'Valor': total_archivos},
                    {'Información': 'Estudiantes Únicos', 'Valor': len(estudiantes_unicos)},
                ])
                resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
                self.log("   ✅ Hoja 'Resumen Ejecutivo' creada")
                
                # Lista de estudiantes
                if estudiantes_unicos:
                    estudiantes_df = pd.DataFrame([
                        {'Estudiante': estudiante} for estudiante in sorted(estudiantes_unicos)
                    ])
                    estudiantes_df.to_excel(writer, sheet_name='Lista de Estudiantes', index=False)
                    self.log("   ✅ Hoja 'Lista de Estudiantes' creada")
                
                # Formatear
                workbook = writer.book
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#1E3A8A',
                    'font_color': 'white',
                    'border': 1
                })
                
                for sheet_name in ['Reporte de Entregas', 'Resumen Ejecutivo', 'Lista de Estudiantes']:
                    if sheet_name in writer.sheets:
                        worksheet = writer.sheets[sheet_name]
                        worksheet.autofit()
            
            self.log("✅ REPORTE EXCEL GENERADO EXITOSAMENTE!")
            self.log(f"📁 Archivo: {filename}")
            self.log(f"📊 ESTADÍSTICAS FINALES:")
            self.log(f"   • Módulos analizados: {len(datos_entregas)}")
            self.log(f"   • Módulos con entregas: {modulos_activos}")
            self.log(f"   • Archivos procesados: {total_archivos}")
            self.log(f"   • Estudiantes únicos: {len(estudiantes_unicos)}")
            
            # Actualizar interfaz
            result = {
                'filename': filename,
                'modules': len(datos_entregas),
                'active_modules': modulos_activos,
                'files': total_archivos,
                'students': len(estudiantes_unicos)
            }
            
            self.root.after(0, lambda: self.report_completed(result))
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ ERROR generando reporte:")
            self.log(f"   {error_msg[:100]}...")
            self.root.after(0, lambda: self.report_error(error_msg))
    
    def report_completed(self, result):
        """Callback cuando el reporte termina"""
        self.report_button.config(state=tk.NORMAL, text="📊 2. GENERAR REPORTE EXCEL")
        
        message = f"""✅ REPORTE EXCEL GENERADO EXITOSAMENTE
        
📁 Archivo: {result['filename']}

📊 Estadísticas Completas:
• {result['modules']} módulos analizados
• {result['active_modules']} módulos con entregas  
• {result['files']} archivos procesados
• {result['students']} estudiantes únicos detectados

📋 El archivo contiene:
• Hoja 'Reporte de Entregas' - Detalle por módulo
• Hoja 'Resumen Ejecutivo' - Estadísticas generales
• Hoja 'Lista de Estudiantes' - Todos los estudiantes

¿Quieres abrir el archivo Excel ahora?"""
        
        if messagebox.askyesno("🎉 Reporte Completado", message):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(result['filename'])
                    self.log(f"📂 Abriendo archivo en Windows...")
                else:  # macOS
                    subprocess.run(['open', result['filename']])
                    self.log(f"📂 Abriendo archivo en macOS...")
            except Exception as e:
                self.log(f"⚠️ No se pudo abrir automáticamente: {e}")
                messagebox.showinfo("Información", f"Abre manualmente: {result['filename']}")
    
    def report_error(self, error):
        """Callback cuando hay error en reporte"""
        self.report_button.config(state=tk.NORMAL, text="📊 2. GENERAR REPORTE EXCEL")
        
        messagebox.showerror(
            "❌ Error Generando Reporte",
            f"No se pudo generar el reporte:\\n\\n"
            f"Error: {error[:150]}...\\n\\n"
            f"💡 Sugerencias:\\n"
            f"• Intenta primero 'Rastrear Google Drive'\\n"
            f"• Verifica tu conexión a internet\\n"
            f"• Revisa el terminal para más detalles"
        )
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

def main():
    """Función principal"""
    try:
        app = AcademiaJeanAppTerminal()
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"Error iniciando la aplicación:\\n\\n{str(e)}\\n\\n{traceback.format_exc()}"
        
        # Intentar mostrar error en ventana
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Error Fatal", error_msg)
        except:
            print(error_msg)

if __name__ == "__main__":
    main()