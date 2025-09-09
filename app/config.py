"""
Configuración central del sistema
"""
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración central de la aplicación"""
    
    # Paths base
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    TEMP_DIR = BASE_DIR / "temp"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # Google Drive
    AUTH_METHOD = os.getenv("AUTH_METHOD", "service_account")
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    GOOGLE_OAUTH_CREDENTIALS = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "")
    
    # File handling
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,pdf").split(",")
    ALLOWED_MIME_TYPES = os.getenv("ALLOWED_MIME_TYPES", "image/jpeg,image/png,application/pdf").split(",")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Email configuration (Gmail)
    GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "")
    GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "")
    REPORT_SENDER = os.getenv("REPORT_SENDER", "darmcastiblanco@gmail.com")
    
    @property
    def REPORT_RECIPIENTS(self) -> List[str]:
        """Lista de destinatarios de reportes"""
        recipients = os.getenv("REPORT_RECIPIENTS", "")
        return [email.strip() for email in recipients.split(",") if email.strip()]
    
    # Report configuration
    DEFAULT_INTERVAL_DAYS = int(os.getenv("DEFAULT_INTERVAL_DAYS", "15"))
    LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "30"))
    
    # Application settings
    TZ = os.getenv("TZ", "America/Bogota")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # CSV Paths
    MODULES_CSV_PATH = os.getenv("MODULES_CSV_PATH", str(DATA_DIR / "modules.csv"))
    STUDENTS_CSV_PATH = os.getenv("STUDENTS_CSV_PATH", str(DATA_DIR / "students.csv"))
    
    def __init__(self):
        """Crear directorios necesarios si no existen"""
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.TEMP_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validar que la configuración esté completa
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL no está configurado")
        
        if self.AUTH_METHOD == "service_account":
            if not self.GOOGLE_SERVICE_ACCOUNT_JSON:
                errors.append("GOOGLE_SERVICE_ACCOUNT_JSON no está configurado")
            elif not Path(self.GOOGLE_SERVICE_ACCOUNT_JSON).exists():
                errors.append(f"Archivo de service account no existe: {self.GOOGLE_SERVICE_ACCOUNT_JSON}")
        
        if not self.GMAIL_CREDENTIALS_PATH and not self.GMAIL_TOKEN_PATH:
            errors.append("Configuración de Gmail no está completa")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> dict:
        """Obtener resumen de configuración (sin datos sensibles)"""
        return {
            "database_configured": bool(self.DATABASE_URL),
            "google_auth_method": self.AUTH_METHOD,
            "allowed_extensions": self.ALLOWED_EXTENSIONS,
            "report_sender": self.REPORT_SENDER,
            "report_recipients_count": len(self.REPORT_RECIPIENTS),
            "default_interval_days": self.DEFAULT_INTERVAL_DAYS,
            "timezone": self.TZ,
            "debug_mode": self.DEBUG
        }

# Instancia global de configuración
config = Config()