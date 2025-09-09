"""
📧 EMAIL SENDER - Jean Academy Analytics
=======================================
Módulo para envío automático de reportes por email.
Soporta Gmail SMTP con App Password.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailSender:
    """Envía reportes por email usando Gmail SMTP."""
    
    def __init__(self):
        # Configuración SMTP Gmail
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # Credenciales desde variables de entorno
        self.sender_email = os.getenv('SENDER_EMAIL', 'darmcastiblanco@gmail.com')
        self.sender_password = os.getenv('SENDER_PASSWORD')  # Gmail App Password
        
        if not self.sender_password:
            logger.warning("⚠️ SENDER_PASSWORD no configurado - emails no funcionarán")
    
    def send_report_email(self, recipient_email: str, excel_file_path: str, 
                         report_period_days: int = 30) -> bool:
        """
        Envía reporte Excel por email.
        
        Args:
            recipient_email: Destinatario del reporte
            excel_file_path: Ruta del archivo Excel a adjuntar
            report_period_days: Período del reporte en días
            
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            if not self.sender_password:
                logger.error("❌ No se puede enviar email - SENDER_PASSWORD no configurado")
                return False
            
            if not Path(excel_file_path).exists():
                logger.error(f"❌ Archivo no encontrado: {excel_file_path}")
                return False
            
            logger.info(f"📧 Preparando email para {recipient_email}...")
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"📊 Reporte Académico Jean Academy - {report_period_days} días"
            
            # Cuerpo del email
            body = self._create_email_body(report_period_days)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Adjuntar archivo Excel
            self._attach_excel_file(msg, excel_file_path)
            
            # Enviar email
            success = self._send_email(msg, recipient_email)
            
            if success:
                logger.info(f"✅ Email enviado exitosamente a {recipient_email}")
                return True
            else:
                logger.error("❌ Error enviando email")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en send_report_email: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_email_body(self, report_period_days: int) -> str:
        """Crea el cuerpo del email con formato profesional."""
        current_date = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        return f"""📚 REPORTE AUTOMATICO - JEAN ACADEMY
===================================

¡Hola! Te enviamos el reporte automático de actividad académica.

📊 DETALLES DEL REPORTE:
• Período analizado: Últimos {report_period_days} días
• Fecha de generación: {current_date}
• Estado del sistema: ✅ Completamente funcional

📁 CONTENIDO DEL ARCHIVO EXCEL:
El archivo adjunto contiene 5 hojas profesionales con:

📋 Hoja 1 - Resumen Ejecutivo:
   • KPIs principales de la academia
   • Métricas de estudiantes y módulos
   • Gráfico de estudiantes más activos

📚 Hoja 2 - Detalle de Módulos:
   • Lista completa de módulos configurados  
   • Número de estudiantes por módulo
   • Entregas procesadas por módulo
   • Última actividad registrada

👥 Hoja 3 - Estudiantes:
   • Lista de todos los estudiantes registrados
   • Progreso individual por estudiante
   • Módulos completados
   • Porcentaje de avance calculado

📝 Hoja 4 - Entregas Recientes:
   • Archivos procesados en el período
   • Información de cada entrega
   • Estudiante que realizó la entrega
   • Fecha y hora de detección

📈 Hoja 5 - Estadísticas y Gráficos:
   • Tendencias de actividad diaria
   • Gráficos de entregas por período
   • Estadísticas de participación

🎯 ACCIONES RECOMENDADAS:
1. Revisa el resumen ejecutivo para métricas clave
2. Analiza el progreso individual de estudiantes
3. Identifica módulos con poca actividad
4. Contacta estudiantes menos activos si es necesario

🔄 PRÓXIMO REPORTE:
Este reporte se genera automáticamente cada {report_period_days} días.
No necesitas hacer nada, el sistema funciona de forma independiente.

🆘 SOPORTE:
Si necesitas ayuda o cambios en la configuración:
• Responde a este email
• Incluye detalles específicos de lo que necesitas

🤖 Reporte generado automáticamente por Jean Academy Analytics
💻 Desarrollado con Claude Code
🌐 Sistema ejecutándose en la nube 24/7

¡Gracias por usar Jean Academy Analytics!
"""
    
    def _attach_excel_file(self, msg: MIMEMultipart, excel_file_path: str):
        """Adjunta el archivo Excel al mensaje."""
        try:
            with open(excel_file_path, "rb") as attachment:
                part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            
            filename = Path(excel_file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= "{filename}"'
            )
            
            msg.attach(part)
            logger.info(f"📎 Archivo adjuntado: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error adjuntando archivo: {e}")
            raise
    
    def _send_email(self, msg: MIMEMultipart, recipient_email: str) -> bool:
        """Envía el email usando SMTP."""
        try:
            logger.info("🔌 Conectando a servidor SMTP Gmail...")
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Habilitar encriptación TLS
            
            logger.info("🔐 Autenticando con Gmail...")
            server.login(self.sender_email, self.sender_password)
            
            logger.info("📨 Enviando mensaje...")
            server.sendmail(self.sender_email, recipient_email, msg.as_string())
            server.quit()
            
            logger.info("✅ Email enviado exitosamente")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación Gmail: {e}")
            logger.error("💡 Verifica que uses App Password, no la contraseña normal")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return False
    
    def test_email_config(self) -> bool:
        """
        Prueba la configuración de email sin enviar mensaje.
        
        Returns:
            bool: True si la configuración es válida
        """
        try:
            if not self.sender_password:
                logger.error("❌ SENDER_PASSWORD no configurado")
                return False
            
            logger.info("🧪 Probando configuración de email...")
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            
            logger.info("✅ Configuración de email válida")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en configuración de email: {e}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """
        Envía un email de prueba sin archivos adjuntos.
        
        Args:
            recipient_email: Destinatario del email de prueba
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            logger.info(f"🧪 Enviando email de prueba a {recipient_email}...")
            
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "🧪 Prueba - Jean Academy Analytics"
            
            test_body = f"""🧪 EMAIL DE PRUEBA - JEAN ACADEMY ANALYTICS

¡Hola!

Este es un email de prueba para verificar que el sistema de envío 
automático de reportes está funcionando correctamente.

✅ Si recibes este mensaje, significa que:
• La configuración de Gmail está correcta
• El servidor SMTP está funcionando
• Las credenciales son válidas
• El sistema está listo para enviar reportes automáticos

📊 PRÓXIMO PASO:
El sistema comenzará a enviar reportes reales según la configuración:
• Frecuencia configurada en el wizard
• Reportes Excel completos con estadísticas
• Envío automático sin intervención manual

🎓 Jean Academy Analytics está listo para funcionar!

Fecha y hora de prueba: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
🤖 Sistema automático desarrollado con Claude Code
"""
            
            msg.attach(MIMEText(test_body, 'plain', 'utf-8'))
            
            success = self._send_email(msg, recipient_email)
            
            if success:
                logger.info("✅ Email de prueba enviado exitosamente")
                return True
            else:
                logger.error("❌ Error enviando email de prueba")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en send_test_email: {e}")
            return False


# Función de conveniencia para usar desde otros módulos
def send_report_email(recipient: str, excel_file: str, period_days: int = 30) -> bool:
    """Función de conveniencia para enviar reportes."""
    sender = EmailSender()
    return sender.send_report_email(recipient, excel_file, period_days)


def test_email_setup(recipient: str) -> bool:
    """Función de conveniencia para probar configuración de email."""
    sender = EmailSender()
    return sender.send_test_email(recipient)


# Script de prueba standalone
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Uso: python emailer.py <email_destinatario>")
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    
    print("🧪 PROBANDO CONFIGURACION DE EMAIL")
    print("=" * 40)
    
    sender = EmailSender()
    
    # Probar configuración
    if sender.test_email_config():
        print("✅ Configuración válida")
        
        # Enviar email de prueba
        if sender.send_test_email(recipient_email):
            print(f"✅ Email de prueba enviado a {recipient_email}")
            print("📧 Revisa tu bandeja de entrada (y spam)")
        else:
            print("❌ Error enviando email de prueba")
    else:
        print("❌ Error en configuración de email")
        print("💡 Configura SENDER_PASSWORD con tu Gmail App Password")