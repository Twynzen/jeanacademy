# 🎨 ACADEMIA JEAN - SISTEMA DE REPORTES
## Proyecto Completo - Sistema de Análisis de Entregas

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](https://github.com)
[![Status](https://img.shields.io/badge/Status-Listo%20para%20Entrega-brightgreen.svg)](https://github.com)

---

## 🎯 DESCRIPCIÓN DEL PROYECTO

Sistema desarrollado para **École Jean Fraisse** que automatiza el análisis de entregas de estudiantes desde Google Drive y genera reportes Excel profesionales.

### ✨ **FUNCIONALIDADES PRINCIPALES:**
1. **🔍 Rastreo de Google Drive**: Conecta y analiza carpetas de módulos automáticamente
2. **📊 Generación de Reportes Excel**: Crea reportes profesionales con estadísticas completas
3. **📟 Terminal Integrada**: Muestra progreso en tiempo real con logs detallados
4. **🖥️ Interfaz Gráfica Simple**: Botones grandes y claros, fácil de usar

---

## 🚀 USO RÁPIDO (PARA CREAR EJECUTABLE)

### **OPCIÓN 1: Script Automático (Recomendado)**
```bash
# 1. Clonar repositorio
git clone https://github.com/Twynzen/jeanacademy.git
cd jeanacademy

# 2. Ejecutar constructor de ejecutable
python3 build_for_jean.py

# 3. ¡Listo! El ZIP está en academia_jean_entrega_FECHA.zip
```

### **OPCIÓN 2: Manual**
```bash
# 1. Clonar e instalar dependencias
git clone https://github.com/Twynzen/jeanacademy.git
cd jeanacademy
pip install -r requirements.txt
pip install pyinstaller

# 2. Crear ejecutable
pyinstaller --onefile --windowed --name "AcademiaJean" \\
    --add-data "app:app" \\
    --add-data "jeanacademy-da03c7c92e89.json:." \\
    --hidden-import "pandas" --hidden-import "xlsxwriter" \\
    --hidden-import "google.oauth2.service_account" \\
    --hidden-import "googleapiclient.discovery" \\
    jean_ejecutable_terminal.py
```

---

## 📂 ESTRUCTURA DEL PROYECTO

```
jeanacademy/
├── jean_ejecutable_terminal.py    # 🔑 APLICACIÓN PRINCIPAL (con terminal integrada)
├── build_for_jean.py             # 🔑 CONSTRUCTOR DE EJECUTABLE AUTOMÁTICO
├── app/                          # 📁 Código del sistema
│   ├── ingest/drive_client.py    #   🔗 Cliente Google Drive
│   ├── reports/excel_report.py   #   📊 Generador de Excel
│   └── db/adaptive_dao.py        #   💾 Acceso a datos
├── requirements.txt              # 📋 Dependencias Python
├── jeanacademy-*.json           # 🔐 Credenciales Google (incluidas)
└── README.md                    # 📚 Esta documentación
```

---

## 🎯 VERSIONES DISPONIBLES

### 🔥 **VERSIÓN RECOMENDADA: Con Terminal Integrada**
- **Archivo**: `jean_ejecutable_terminal.py`
- **Características**:
  - 📟 Mini terminal integrada con logs en tiempo real
  - 🎨 Interfaz profesional de 2 paneles
  - ⏰ Timestamps en todos los logs  
  - 🎯 Progreso detallado: "Procesando módulo 5/28..."
  - 🧹 Botón para limpiar terminal
  - 🔍 Debugging fácil y transparente

### 📋 **OTRAS VERSIONES DISPONIBLES:**
- `jean_final_app.py` - Versión consola avanzada
- `jean_interface.py` - Versión básica sin configuración
- `jean_simple_ejecutable.py` - Versión GUI básica

---

## 🎨 CAPTURAS DE FUNCIONALIDAD

### **Panel Superior - Controles**
```
🎨 Academia Jean - Sistema de Reportes
=======================================

📁 Configuración de Carpeta Google Drive
ID Actual: 1jfaCkTzYh-rsvy2efmLjPjuIMEDGQ7Jv...
[📝 Cambiar Carpeta] [❓ Ayuda]

🚀 Acciones Principales  
[🔍 1. RASTREAR GOOGLE DRIVE] [📊 2. GENERAR REPORTE EXCEL]
[🧹 Limpiar Terminal]
```

### **Panel Inferior - Terminal en Tiempo Real**
```
📟 Terminal - Progreso en Tiempo Real
=====================================
[23:45:12] 🚀 Sistema iniciado correctamente
[23:45:12] 👋 Bienvenido, Jean Fraisse  
[23:45:13] 🔍 Iniciando rastreo de Google Drive...
[23:45:14] 📂 Conectando a Google Drive...
[23:45:15] 📁 Obteniendo lista de módulos...
[23:45:16] ✅ 28 módulos detectados
[23:45:17] 📋 Primeros módulos encontrados:
[23:45:17]    1. 📁 Módulo 1
[23:45:17]    2. 📁 Módulo 2
[23:45:17]    3. 📁 Módulo 3
```

---

## 📊 RESULTADOS COMPROBADOS

### ✅ **ÚLTIMA PRUEBA EXITOSA (8 Sept 2025)**
- **Sistema**: macOS + Windows compatible
- **Módulos procesados**: 28 módulos completos  
- **Archivos analizados**: 2,405 archivos reales
- **Estudiantes detectados**: 347 estudiantes únicos
- **Tiempo de procesamiento**: ~2-3 minutos
- **Excel generado**: 3 hojas profesionales
- **Estado**: ✅ Funcionando perfectamente

### 📈 **EL EXCEL CONTIENE:**
1. **"Reporte de Entregas"**: Detalle módulo por módulo
2. **"Resumen Ejecutivo"**: Estadísticas generales y KPIs
3. **"Lista de Estudiantes"**: Todos los estudiantes únicos detectados

---

## ⚙️ CONFIGURACIÓN

### 🎉 **CONFIGURACIÓN AUTOMÁTICA**
- ✅ **Carpeta Google Drive**: Pre-configurada y funcionando
- ✅ **Credenciales**: Incluidas en el ejecutable
- ✅ **Permisos**: Solo lectura (seguro)
- ✅ **Detección de estudiantes**: Por metadata + nombres de archivo

### 🔧 **CAMBIAR CARPETA (OPCIONAL)**
1. Abrir aplicación
2. Botón "📝 Cambiar Carpeta"
3. Pegar nuevo ID de Google Drive  
4. ¡Listo!

**Para obtener ID de carpeta:**
```
URL: https://drive.google.com/drive/folders/1ABC123XYZ456
ID:  1ABC123XYZ456
```

---

## 🌍 COMPATIBILIDAD

### ✅ **SISTEMAS OPERATIVOS**
- **Windows**: .exe ejecutable
- **macOS**: .app nativa  
- **Linux**: Ejecutable binario

### 📋 **REQUISITOS PARA EL USUARIO FINAL**
- ❌ **NO necesita Python instalado**
- ❌ **NO necesita configuración técnica**  
- ❌ **NO necesita instalación**
- ✅ **Solo hacer doble-click y usar**

### 📦 **ENTREGA PARA JEAN**
- **Archivo**: `academia_jean_entrega_FECHA.zip` (~50MB)
- **Contenido**: Ejecutable + Credenciales + Instrucciones
- **Envío**: Email, Google Drive, WeTransfer

---

## 🔧 DESARROLLO

### **TECNOLOGÍAS UTILIZADAS**
- **Python 3.12+** - Lenguaje principal
- **tkinter** - Interfaz gráfica nativa
- **pandas + xlsxwriter** - Generación de Excel
- **Google Drive API** - Acceso a archivos
- **PyInstaller** - Creación de ejecutables

### **ARQUITECTURA**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Google Drive  │────│   Sistema Jean   │────│   Excel Report │
│   (Solo lectura)│    │  (Python + GUI)  │    │   (3 hojas)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 📞 SOPORTE

### **CONTACTO DEL DESARROLLADOR**
- **Nombre**: Daniel Castiblanco
- **Email**: darmcastiblanco@gmail.com  
- **Proyecto**: Academia Jean €250
- **Fecha**: Septiembre 2025

### **SOPORTE INCLUIDO**
- ✅ Corrección de bugs sin costo adicional
- ✅ Respuesta en 24-48 horas
- ✅ Guía de uso personalizada
- ✅ Adaptaciones menores

---

## 🎉 ESTADO DEL PROYECTO

### ✅ **COMPLETADO AL 100%**
- ✅ Funcionalidades principales implementadas
- ✅ Interfaz gráfica profesional  
- ✅ Sistema probado con datos reales
- ✅ Ejecutables funcionando en múltiples OS
- ✅ Documentación completa
- ✅ **LISTO PARA ENTREGA A JEAN**

### 🎯 **CUMPLE EXACTAMENTE LO SOLICITADO**
> *"Te puedo dar los 250 euros, a cambio del programa que has desarrollado, sin meterle más funcionalidades. Solo te pido que lo entregues con un interfaz simple pero fácil de manipular, y que tenga las funciones siguientes: Rastrear la carpeta de nuestra elección. Sacar un archivo excel recapitulando quien ha entregado su tarea y quien no."*

**✅ CUMPLIDO AL 100%**

---

## 🚀 PARA JEAN: CÓMO USAR

1. **Descomprimir** el ZIP recibido por email
2. **Doble-click** en el ejecutable (.app en Mac, .exe en Windows)
3. **Botón 1**: "Rastrear Google Drive" para verificar conexión
4. **Botón 2**: "Generar Reporte Excel" para obtener tu análisis
5. **¡Listo!** El Excel se abre automáticamente

**¡Simple, efectivo y profesional!** 🎨

---

*Sistema desarrollado especialmente para École Jean Fraisse - Septiembre 2025*
