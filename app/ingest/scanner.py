import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dateutil.parser import parse as parse_date

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.db.dao import dao
from app.ingest.drive_client import GoogleDriveClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModuleScanner:
    def __init__(self):
        self.drive_client = GoogleDriveClient()
        self.dao = dao
        
        # Patrones para identificar estudiantes por email o nombre
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Tipos MIME de archivos que consideramos entregas
        self.valid_mime_types = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/bmp',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
            'application/msword',  # .doc
            'text/plain'  # .txt
        ]
        
        logger.info("🔄 Scanner de módulos inicializado")
    
    def identify_student_from_file(self, file_data: Dict) -> Optional[Tuple[str, str]]:
        """
        Identifica estudiante a partir de metadata del archivo.
        Retorna tuple (nombre, email) si se puede identificar, None si no.
        """
        try:
            # 1. Intentar obtener del usuario que modificó por última vez
            if 'lastModifyingUser' in file_data:
                user = file_data['lastModifyingUser']
                email = user.get('emailAddress', '')
                name = user.get('displayName', '')
                
                if email and '@' in email:
                    logger.debug(f"  👤 Identificado por lastModifyingUser: {name} ({email})")
                    return (name or email.split('@')[0], email)
            
            # 2. Intentar obtener del propietario
            if 'owners' in file_data and file_data['owners']:
                owner = file_data['owners'][0]  # Primer propietario
                email = owner.get('emailAddress', '')
                name = owner.get('displayName', '')
                
                if email and '@' in email:
                    logger.debug(f"  👤 Identificado por owner: {name} ({email})")
                    return (name or email.split('@')[0], email)
            
            # 3. Buscar email en el nombre del archivo
            filename = file_data.get('name', '')
            email_match = re.search(self.email_pattern, filename)
            if email_match:
                email = email_match.group()
                name = email.split('@')[0]
                logger.debug(f"  👤 Email encontrado en nombre: {name} ({email})")
                return (name, email)
            
            # 4. Intentar extraer nombre del archivo (formato común: "Nombre_Apellido_ejercicio.jpg")
            name_patterns = [
                r'^([A-Za-zÀ-ÿ]+[_\s]+[A-Za-zÀ-ÿ]+)',  # Nombre_Apellido
                r'^([A-Za-zÀ-ÿ\s]+)[-_]',  # Nombre - algo
                r'^([A-Za-zÀ-ÿ\s]+)\.',   # Nombre.extension
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, filename)
                if match:
                    name = match.group(1).replace('_', ' ').strip()
                    if len(name) > 2:  # Nombre debe tener al menos 3 caracteres
                        # Generar email temporal basado en el nombre
                        email = f"{name.lower().replace(' ', '.')}@student.temp"
                        logger.debug(f"  👤 Nombre extraído del archivo: {name} (email temporal)")
                        return (name, email)
            
            logger.debug(f"  ❓ No se pudo identificar estudiante para: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error identificando estudiante: {e}")
            return None
    
    def sync_modules_to_db(self) -> Dict:
        """
        Sincroniza módulos de Google Drive con la base de datos.
        """
        try:
            logger.info("🔄 Sincronizando módulos con la base de datos...")
            
            # Obtener módulos de Google Drive
            drive_modules = self.drive_client.list_folders_in_root()
            
            results = {
                'modules_created': 0,
                'modules_updated': 0,
                'modules_processed': 0,
                'errors': []
            }
            
            for module_folder in drive_modules:
                try:
                    module_name = module_folder['name']
                    drive_folder_id = module_folder['id']
                    
                    logger.info(f"  📚 Procesando módulo: {module_name}")
                    
                    # Verificar si el módulo ya existe en BD
                    existing_modules = self.dao.get_all_modules()
                    existing_module = next(
                        (m for m in existing_modules if m['drive_folder_id'] == drive_folder_id), 
                        None
                    )
                    
                    if existing_module:
                        logger.debug(f"    ✅ Módulo ya existe en BD (ID: {existing_module['id']})")
                        results['modules_updated'] += 1
                    else:
                        # Crear nuevo módulo
                        module_id = self.dao.create_module(
                            name=module_name,
                            drive_folder_id=drive_folder_id,
                            description=f"Módulo importado desde Google Drive: {module_name}"
                        )
                        logger.info(f"    ✅ Nuevo módulo creado (ID: {module_id})")
                        results['modules_created'] += 1
                    
                    results['modules_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando módulo {module_folder.get('name', 'Unknown')}: {e}"
                    logger.error(f"    ❌ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ Sincronización completa: {results['modules_created']} nuevos, {results['modules_updated']} existentes")
            return results
            
        except Exception as e:
            error_msg = f"Error durante sincronización de módulos: {e}"
            logger.error(f"❌ {error_msg}")
            return {'error': error_msg, 'modules_processed': 0}
    
    def scan_module(self, module_id: int) -> Dict:
        """
        Escanea un módulo específico y actualiza la base de datos.
        """
        try:
            logger.info(f"🔍 Escaneando módulo ID: {module_id}")
            
            # Obtener información del módulo de la BD
            module = self.dao.get_module_by_id(module_id)
            if not module:
                raise ValueError(f"Módulo {module_id} no encontrado en la base de datos")
            
            logger.info(f"  📚 Módulo: {module['name']}")
            logger.info(f"  📁 Drive Folder: {module['drive_folder_id']}")
            
            # Obtener archivos del módulo desde Google Drive
            files = self.drive_client.list_files_in_folder(
                module['drive_folder_id'],
                self.valid_mime_types
            )
            
            results = {
                'module_id': module_id,
                'module_name': module['name'],
                'files_found': len(files),
                'students_created': 0,
                'submissions_created': 0,
                'submissions_updated': 0,
                'errors': []
            }
            
            logger.info(f"  📄 Archivos encontrados: {len(files)}")
            
            # Procesar cada archivo
            for i, file_data in enumerate(files, 1):
                try:
                    logger.debug(f"    [{i}/{len(files)}] Procesando: {file_data['name']}")
                    
                    # Identificar estudiante
                    student_info = self.identify_student_from_file(file_data)
                    if not student_info:
                        logger.warning(f"    ⚠️  No se pudo identificar estudiante para: {file_data['name']}")
                        continue
                    
                    student_name, student_email = student_info
                    
                    # Crear/obtener estudiante en BD
                    student_id = self.dao.create_student(student_name, student_email)
                    if self.dao.get_student_by_email(student_email):
                        logger.debug(f"      👤 Estudiante existente: {student_name}")
                    else:
                        logger.info(f"      ✅ Nuevo estudiante: {student_name} ({student_email})")
                        results['students_created'] += 1
                    
                    # Procesar fecha de submisión
                    submitted_at = None
                    if 'modifiedTime' in file_data:
                        try:
                            submitted_at = parse_date(file_data['modifiedTime']).replace(tzinfo=None)
                        except Exception as e:
                            logger.debug(f"      ⚠️  Error parseando fecha: {e}")
                            submitted_at = datetime.now()
                    
                    # Crear/actualizar submission
                    submission_id = self.dao.create_submission(
                        module_id=module_id,
                        student_id=student_id,
                        file_name=file_data['name'],
                        drive_file_id=file_data['id'],
                        file_size=int(file_data.get('size', 0)),
                        mime_type=file_data.get('mimeType', 'unknown'),
                        submitted_at=submitted_at
                    )
                    
                    if submission_id:
                        results['submissions_created'] += 1
                        logger.debug(f"      📝 Submission creada (ID: {submission_id})")
                    else:
                        results['submissions_updated'] += 1
                        logger.debug(f"      📝 Submission actualizada")
                    
                except Exception as e:
                    error_msg = f"Error procesando archivo {file_data.get('name', 'Unknown')}: {e}"
                    logger.error(f"    ❌ {error_msg}")
                    results['errors'].append(error_msg)
            
            # Actualizar timestamp del módulo
            self.dao.update_module_last_scan(module_id)
            
            # Actualizar métricas
            self.dao.update_module_metrics(module_id)
            
            logger.info(f"✅ Escaneo completado: {results['submissions_created']} nuevas submissions, {results['students_created']} nuevos estudiantes")
            
            return results
            
        except Exception as e:
            error_msg = f"Error escaneando módulo {module_id}: {e}"
            logger.error(f"❌ {error_msg}")
            return {'error': error_msg, 'module_id': module_id}
    
    def full_scan(self) -> Dict:
        """
        Ejecuta un escaneo completo de todos los módulos.
        """
        try:
            logger.info("🚀 Iniciando escaneo completo de todos los módulos...")
            
            # Crear log de sincronización
            sync_id = self.dao.create_sync_log('full_scan')
            
            # Primero sincronizar módulos
            sync_results = self.sync_modules_to_db()
            
            # Obtener todos los módulos activos
            modules = self.dao.get_all_modules()
            
            full_results = {
                'sync_id': sync_id,
                'total_modules': len(modules),
                'modules_scanned': 0,
                'total_files': 0,
                'total_submissions': 0,
                'total_students': 0,
                'errors': sync_results.get('errors', []),
                'module_results': {}
            }
            
            # Escanear cada módulo
            for i, module in enumerate(modules, 1):
                try:
                    logger.info(f"📊 [{i}/{len(modules)}] Escaneando módulo: {module['name']}")
                    
                    scan_result = self.scan_module(module['id'])
                    
                    if 'error' not in scan_result:
                        full_results['modules_scanned'] += 1
                        full_results['total_files'] += scan_result['files_found']
                        full_results['total_submissions'] += scan_result['submissions_created']
                        full_results['total_students'] += scan_result['students_created']
                        
                        full_results['module_results'][module['name']] = scan_result
                    else:
                        full_results['errors'].append(scan_result['error'])
                    
                except Exception as e:
                    error_msg = f"Error en módulo {module['name']}: {e}"
                    logger.error(f"  ❌ {error_msg}")
                    full_results['errors'].append(error_msg)
            
            # Actualizar métricas diarias
            self.dao.update_daily_metrics()
            
            # Actualizar log de sincronización
            status = 'completed' if not full_results['errors'] else 'completed_with_errors'
            self.dao.update_sync_log(
                sync_id=sync_id,
                status=status,
                files_processed=full_results['total_files'],
                errors=len(full_results['errors']),
                error_details='; '.join(full_results['errors'][:5]) if full_results['errors'] else None
            )
            
            # Resumen final
            logger.info("=" * 60)
            logger.info("🎉 ESCANEO COMPLETO FINALIZADO")
            logger.info(f"  • Módulos escaneados: {full_results['modules_scanned']}/{full_results['total_modules']}")
            logger.info(f"  • Total archivos procesados: {full_results['total_files']}")
            logger.info(f"  • Nuevas submissions: {full_results['total_submissions']}")
            logger.info(f"  • Nuevos estudiantes: {full_results['total_students']}")
            if full_results['errors']:
                logger.warning(f"  • Errores encontrados: {len(full_results['errors'])}")
            logger.info("=" * 60)
            
            return full_results
            
        except Exception as e:
            error_msg = f"Error durante escaneo completo: {e}"
            logger.error(f"❌ {error_msg}")
            
            # Actualizar log como fallido
            if 'sync_id' in locals():
                self.dao.update_sync_log(
                    sync_id=sync_id,
                    status='failed',
                    error_details=error_msg
                )
            
            return {'error': error_msg}


# Función para pruebas
def test_scanner():
    try:
        scanner = ModuleScanner()
        
        # Primero sincronizar módulos
        logger.info("🔄 Probando sincronización de módulos...")
        sync_result = scanner.sync_modules_to_db()
        logger.info(f"Resultado sync: {sync_result}")
        
        # Luego probar escaneo de un módulo
        modules = scanner.dao.get_all_modules()
        if modules:
            first_module = modules[0]
            logger.info(f"🔍 Probando escaneo del módulo: {first_module['name']}")
            scan_result = scanner.scan_module(first_module['id'])
            logger.info(f"Resultado scan: {scan_result}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en pruebas: {e}")
        return False


if __name__ == "__main__":
    test_scanner()