#!/usr/bin/env python3
"""
🚀 JEAN ACADEMY - MAIN JOB (CLOUD WORKER)
=========================================
Job principal para ejecutar reportes automáticos en la nube.
Este script se ejecuta en Railway/Fly.io según el scheduler configurado.

Flujo:
1. Lee configuración desde variables de entorno
2. Genera reporte Excel con datos actualizados
3. Envía reporte por email automáticamente
4. Registra resultado en base de datos

Autor: Claude Code
Versión: 1.0
Fecha: 09/08/2025
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import traceback

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.reports.excel_report import ExcelReportGenerator
    from app.notify.emailer import EmailSender
    from app.db.adaptive_dao import adaptive_dao
    from app.utils.logging import setup_logging
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de estar en el directorio correcto y tener las dependencias instaladas")
    sys.exit(1)

# Configurar logging para la nube
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class AutomatedReportJob:
    """Job principal para reportes automáticos en la nube."""
    
    def __init__(self):
        self.load_config_from_env()
        self.validate_config()
        
    def load_config_from_env(self):
        """Carga configuración desde variables de entorno."""
        logger.info("⚙️ Cargando configuración desde variables de entorno...")
        
        self.config = {
            'recipient_email': os.getenv('EMAIL_RECIPIENT'),
            'report_interval_days': int(os.getenv('REPORT_INTERVAL_DAYS', 15)),
            'sender_email': os.getenv('SENDER_EMAIL', 'darmcastiblanco@gmail.com'),
            'sender_password': os.getenv('SENDER_PASSWORD'),
            'database_url': os.getenv('DATABASE_URL'),
            'drive_folder_id': os.getenv('DRIVE_FOLDER_ID'),
            'google_credentials': os.getenv('GOOGLE_CREDENTIALS'),
        }
        
        logger.info(f"📧 Email destinatario: {self.config['recipient_email']}")
        logger.info(f"⏰ Intervalo de reportes: {self.config['report_interval_days']} días")
        logger.info(f"🗄️ Base de datos: {'✅ Configurada' if self.config['database_url'] else '❌ No configurada'}")
        logger.info(f"📁 Google Drive: {'✅ Configurado' if self.config['drive_folder_id'] else '❌ No configurado'}")
        
    def validate_config(self):
        """Valida que toda la configuración necesaria esté presente."""
        logger.info("✅ Validando configuración...")
        
        required_vars = [
            ('EMAIL_RECIPIENT', self.config['recipient_email']),
            ('DATABASE_URL', self.config['database_url']),
            ('DRIVE_FOLDER_ID', self.config['drive_folder_id']),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
                logger.error(f"❌ Variable requerida no configurada: {var_name}")
        
        if missing_vars:
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing_vars)}")
        
        # Validar email
        if '@' not in self.config['recipient_email']:
            raise ValueError(f"Email destinatario inválido: {self.config['recipient_email']}")
        
        logger.info("✅ Configuración validada correctamente")
    
    def run_full_report_cycle(self) -> bool:
        """
        Ejecuta el ciclo completo de reporte automático.
        
        Returns:
            bool: True si todo fue exitoso, False en caso contrario
        """
        sync_log_id = None
        
        try:
            logger.info("🚀 INICIANDO CICLO DE REPORTE AUTOMATICO")
            logger.info("=" * 60)
            
            # 1. Registrar inicio en base de datos
            sync_log_id = self._create_sync_log()
            
            # 2. Generar reporte Excel
            excel_file_path = self._generate_excel_report()
            
            # 3. Enviar por email
            email_sent = self._send_email_report(excel_file_path)
            
            # 4. Registrar resultado final
            if email_sent:
                self._update_sync_log_success(sync_log_id, excel_file_path)
                logger.info("🎉 REPORTE AUTOMATICO COMPLETADO EXITOSAMENTE")
                return True
            else:
                self._update_sync_log_failure(sync_log_id, "Error enviando email")
                logger.error("❌ FALLO EN ENVIO DE EMAIL")
                return False
                
        except Exception as e:
            error_msg = f"Error en ciclo de reporte: {e}"
            logger.error(f"❌ {error_msg}")
            traceback.print_exc()
            
            if sync_log_id:
                self._update_sync_log_failure(sync_log_id, error_msg)
            
            return False
    
    def _create_sync_log(self) -> str:
        """Crea registro de inicio del job."""
        try:
            logger.info("📝 Registrando inicio de job en base de datos...")
            sync_log_id = adaptive_dao.create_sync_log('automated_cloud_report')
            logger.info(f"✅ Sync log creado: ID {sync_log_id}")
            return sync_log_id
        except Exception as e:
            logger.warning(f"⚠️ Error creando sync log: {e}")
            return None
    
    def _generate_excel_report(self) -> str:
        """Genera el reporte Excel."""
        logger.info("📊 GENERANDO REPORTE EXCEL")
        logger.info("-" * 30)
        
        try:
            # Instanciar generador de reportes
            report_generator = ExcelReportGenerator()
            
            # Generar reporte
            logger.info(f"📈 Generando reporte para últimos {self.config['report_interval_days']} días...")
            excel_file_path = report_generator.generate_full_report(
                period_days=self.config['report_interval_days']
            )
            
            # Verificar que el archivo se creó
            if not Path(excel_file_path).exists():
                raise FileNotFoundError(f"Reporte no se generó: {excel_file_path}")
            
            # Obtener tamaño del archivo
            file_size = Path(excel_file_path).stat().st_size / 1024  # KB
            logger.info(f"✅ Reporte Excel generado exitosamente")
            logger.info(f"📁 Archivo: {excel_file_path}")
            logger.info(f"📊 Tamaño: {file_size:.1f} KB")
            
            return excel_file_path
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte Excel: {e}")
            raise
    
    def _send_email_report(self, excel_file_path: str) -> bool:
        """Envía el reporte por email."""
        logger.info("📧 ENVIANDO REPORTE POR EMAIL")
        logger.info("-" * 30)
        
        try:
            # Instanciar sender de emails
            email_sender = EmailSender()
            
            # Verificar configuración de email
            if not email_sender.test_email_config():
                logger.error("❌ Configuración de email inválida")
                return False
            
            # Enviar email con reporte
            logger.info(f"📨 Enviando reporte a {self.config['recipient_email']}...")
            
            email_sent = email_sender.send_report_email(
                recipient_email=self.config['recipient_email'],
                excel_file_path=excel_file_path,
                report_period_days=self.config['report_interval_days']
            )
            
            if email_sent:
                logger.info("✅ Email enviado exitosamente")
                return True
            else:
                logger.error("❌ Error enviando email")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en envío de email: {e}")
            return False
    
    def _update_sync_log_success(self, sync_log_id: str, excel_file_path: str):
        """Actualiza sync log con resultado exitoso."""
        if not sync_log_id:
            return
            
        try:
            logger.info("📝 Actualizando registro de job (éxito)...")
            
            adaptive_dao.update_sync_log(
                sync_log_id=sync_log_id,
                status='completed',
                files_processed=1,
                completed_at=datetime.now()
            )
            
            logger.info("✅ Registro actualizado correctamente")
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando sync log: {e}")
    
    def _update_sync_log_failure(self, sync_log_id: str, error_message: str):
        """Actualiza sync log con resultado de error."""
        if not sync_log_id:
            return
            
        try:
            logger.info("📝 Actualizando registro de job (error)...")
            
            adaptive_dao.update_sync_log(
                sync_log_id=sync_log_id,
                status='failed',
                error_details=error_message,
                completed_at=datetime.now()
            )
            
            logger.info("✅ Registro de error actualizado")
            
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando sync log de fallo: {e}")
    
    def get_system_status(self) -> dict:
        """Obtiene estado actual del sistema para monitoreo."""
        try:
            logger.info("📊 Obteniendo estado del sistema...")
            
            # Estadísticas de base de datos
            stats = adaptive_dao.get_statistics()
            
            # Estado de conexiones
            db_connected = adaptive_dao.test_connection()
            
            # Configuración de email
            email_sender = EmailSender()
            email_configured = bool(email_sender.sender_password)
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'database_connected': db_connected,
                'email_configured': email_configured,
                'recipient_email': self.config['recipient_email'],
                'report_interval_days': self.config['report_interval_days'],
                'statistics': stats,
                'config_valid': True
            }
            
            logger.info("✅ Estado del sistema obtenido")
            return status
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del sistema: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'config_valid': False
            }


def run_automated_report() -> int:
    """
    Función principal para ejecutar desde la línea de comandos.
    
    Returns:
        int: 0 si éxito, 1 si error (para exit code)
    """
    try:
        logger.info("🎓 JEAN ACADEMY - AUTOMATED REPORT JOB")
        logger.info("🤖 Desarrollado con Claude Code")
        logger.info("=" * 60)
        logger.info(f"🕐 Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Crear y ejecutar job
        job = AutomatedReportJob()
        success = job.run_full_report_cycle()
        
        if success:
            logger.info("🎉 JOB COMPLETADO EXITOSAMENTE")
            return 0
        else:
            logger.error("❌ JOB FALLÓ")
            return 1
            
    except Exception as e:
        logger.error(f"❌ ERROR CRÍTICO EN MAIN JOB: {e}")
        traceback.print_exc()
        return 1


def get_status() -> int:
    """
    Función para obtener estado del sistema (health check).
    
    Returns:
        int: 0 si todo OK, 1 si hay problemas
    """
    try:
        job = AutomatedReportJob()
        status = job.get_system_status()
        
        print("📊 ESTADO DEL SISTEMA:")
        print("=" * 30)
        
        for key, value in status.items():
            if key == 'statistics':
                print(f"📈 Estadísticas:")
                for stat_key, stat_value in value.items():
                    print(f"   • {stat_key}: {stat_value}")
            else:
                print(f"• {key}: {value}")
        
        if status.get('config_valid') and status.get('database_connected'):
            logger.info("✅ Sistema funcionando correctamente")
            return 0
        else:
            logger.warning("⚠️ Sistema tiene problemas de configuración")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {e}")
        return 1


if __name__ == "__main__":
    # Parsear argumentos de línea de comandos
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'status':
            # Health check
            exit_code = get_status()
        elif command == 'test':
            # Prueba rápida sin enviar email
            logger.info("🧪 MODO DE PRUEBA")
            try:
                job = AutomatedReportJob()
                status = job.get_system_status()
                print("✅ Configuración válida para ejecutar reportes")
                exit_code = 0
            except Exception as e:
                print(f"❌ Error en configuración: {e}")
                exit_code = 1
        else:
            print(f"❌ Comando desconocido: {command}")
            print("💡 Comandos disponibles: status, test")
            exit_code = 1
    else:
        # Ejecutar reporte automático (comportamiento por defecto)
        exit_code = run_automated_report()
    
    sys.exit(exit_code)