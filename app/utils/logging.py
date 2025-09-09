"""
Sistema de logging para la aplicación
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from app.config import config

# Crear directorio de logs si no existe
log_dir = Path(config.LOGS_DIR)
log_dir.mkdir(exist_ok=True)

# Configurar formato de logs
log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Configurar handler para archivo
log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter(log_format, date_format))

# Configurar handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(log_format, date_format))

# Configurar logger principal
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    handlers=[file_handler, console_handler]
)

# Logger principal de la aplicación
logger = logging.getLogger("JeanAcademy")

# Loggers específicos por módulo
def get_logger(name: str) -> logging.Logger:
    """Obtener un logger específico para un módulo"""
    return logging.getLogger(f"JeanAcademy.{name}")

# Log de inicio
logger.info("="*60)
logger.info("Sistema de Analítica Jean Academy iniciado")
logger.info(f"Nivel de log: {config.LOG_LEVEL}")
logger.info(f"Archivo de log: {log_file}")
logger.info("="*60)