"""
📧 RESEND EMAIL SENDER - Jean Academy Analytics
==============================================
Módulo SIMPLE y FUNCIONAL para envío de reportes con Resend.
NO necesita contraseñas complicadas, solo una API key.
"""

import resend
import os
import logging
from datetime import datetime
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

# Configurar Resend con API key desde .env
resend.api_key = os.getenv('RESEND_API_KEY', 're_SWfMgbqa_BbseM4uvfCNfcBc62yY8qaiE')


class ResendEmailer:
    """Envía reportes por email usando Resend - SIMPLE Y FUNCIONAL."""
    
    def __init__(self):
        # Email remitente (Resend proporciona uno por defecto)
        self.sender_email = "Jean Academy Reports <onboarding@resend.dev>"
        
        # Email destinatario desde .env o por defecto
        # ACTUALIZADO: Ahora funciona con draebdraw@gmail.com (cuenta de colaboradora)
        self.recipient_email = os.getenv('REPORT_RECIPIENT_EMAIL', 'draebdraw@gmail.com')
        
        logger.info(f"📧 Resend configurado - Destinatario: {self.recipient_email}")
    
    def send_report_email(self, excel_file_path: str, recipient_email: str = None) -> bool:
        """
        Envía reporte Excel por email usando Resend.
        
        Args:
            excel_file_path: Ruta del archivo Excel a enviar
            recipient_email: Email destinatario (opcional, usa el configurado por defecto)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Usar destinatario específico o el configurado
            to_email = recipient_email or self.recipient_email
            
            logger.info(f"📤 Enviando reporte a {to_email}...")
            
            # Verificar que el archivo existe
            if not Path(excel_file_path).exists():
                logger.error(f"❌ Archivo no encontrado: {excel_file_path}")
                return False
            
            # Leer el archivo Excel
            with open(excel_file_path, 'rb') as f:
                file_content = f.read()
                file_base64 = base64.b64encode(file_content).decode()
            
            # Nombre del archivo
            filename = Path(excel_file_path).name
            
            # Fecha y hora actual
            current_date = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Crear email con Resend
            response = resend.Emails.send({
                "from": self.sender_email,
                "to": to_email,
                "subject": f"📊 Reporte Jean Academy - {current_date}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1E3A8A;">🎓 Reporte Automático - Jean Academy</h2>
                    
                    <p>¡Hola!</p>
                    
                    <p>Te enviamos el reporte automático de actividad académica.</p>
                    
                    <div style="background: #F3F4F6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #1E3A8A; margin-top: 0;">📊 Contenido del Reporte:</h3>
                        <ul style="color: #4B5563;">
                            <li>✅ Resumen ejecutivo con KPIs principales</li>
                            <li>📚 Detalle de actividad por módulo</li>
                            <li>👥 Progreso individual de estudiantes</li>
                            <li>📝 Entregas recientes procesadas</li>
                            <li>📈 Estadísticas y gráficos de tendencias</li>
                        </ul>
                    </div>
                    
                    <p><strong>📁 Archivo adjunto:</strong> {filename}</p>
                    <p><strong>📅 Generado:</strong> {current_date}</p>
                    
                    <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 30px 0;">
                    
                    <p style="color: #6B7280; font-size: 12px;">
                        🤖 Reporte generado automáticamente por Jean Academy Analytics<br>
                        💻 Desarrollado con Claude Code<br>
                        📧 Enviado con Resend
                    </p>
                </div>
                """,
                "attachments": [{
                    "filename": filename,
                    "content": file_base64
                }]
            })
            
            logger.info(f"✅ Email enviado exitosamente - ID: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email con Resend: {e}")
            return False
    
    def send_test_email(self, recipient_email: str = None) -> bool:
        """
        Envía un email de prueba simple.
        
        Args:
            recipient_email: Email destinatario (opcional)
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            to_email = recipient_email or self.recipient_email
            
            logger.info(f"🧪 Enviando email de prueba a {to_email}...")
            
            response = resend.Emails.send({
                "from": self.sender_email,
                "to": to_email,
                "subject": "🧪 Prueba - Jean Academy Analytics",
                "html": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #10B981;">✅ ¡Email de Prueba Exitoso!</h2>
                    
                    <p>Si estás viendo este mensaje, significa que:</p>
                    
                    <ul>
                        <li>✅ Resend está configurado correctamente</li>
                        <li>✅ Los emails funcionan perfectamente</li>
                        <li>✅ Los reportes se enviarán sin problemas</li>
                    </ul>
                    
                    <div style="background: #F0FDF4; padding: 15px; border-radius: 8px; border-left: 4px solid #10B981;">
                        <strong>🎉 ¡El sistema está listo para usar!</strong>
                    </div>
                    
                    <p style="margin-top: 30px; color: #6B7280; font-size: 12px;">
                        🎓 Jean Academy Analytics<br>
                        💻 Desarrollado con Claude Code<br>
                        📧 Powered by Resend
                    </p>
                </div>
                """
            })
            
            logger.info(f"✅ Email de prueba enviado - ID: {response.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email de prueba: {e}")
            return False


# Función principal para usar desde otros módulos
def send_report(excel_file: str, recipient: str = None) -> bool:
    """Envía reporte por email usando Resend."""
    emailer = ResendEmailer()
    return emailer.send_report_email(excel_file, recipient)


# Script de prueba
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🧪 PRUEBA DE RESEND EMAIL")
    print("=" * 60)
    print()
    
    emailer = ResendEmailer()
    
    # Si se pasa un email como argumento, usarlo
    recipient = sys.argv[1] if len(sys.argv) > 1 else None
    
    if emailer.send_test_email(recipient):
        print()
        print("🎉 ¡EMAIL ENVIADO EXITOSAMENTE!")
        print(f"📬 Revisa: {recipient or emailer.recipient_email}")
        print()
        print("✅ El sistema de emails está funcionando perfectamente")
    else:
        print("❌ Error enviando email")
        print("Verifica la API key de Resend en el archivo .env")