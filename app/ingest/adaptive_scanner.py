import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.db.adaptive_dao import adaptive_dao
from app.ingest.drive_client import GoogleDriveClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptiveModuleScanner:
    def __init__(self):
        self.drive_client = GoogleDriveClient()
        self.dao = adaptive_dao
        
        # Mostrar información del schema descubierto
        schema_info = self.dao.get_schema_info()
        logger.info(f"🔍 Schema descubierto: {len(schema_info['tables'])} tablas")
        for table in schema_info['tables']:
            columns = len(schema_info['schemas'][table]['column_names'])
            logger.info(f"  📋 {table}: {columns} columnas")
        
        # Patrones para identificar estudiantes
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Tipos MIME válidos
        self.valid_mime_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ]
        
        logger.info("✅ Scanner adaptativo inicializado")
    
    def _extract_name_from_filename(self, filename: str) -> Optional[str]:
        """Extrae el nombre del estudiante del nombre del archivo."""
        # Patrones para extraer nombres del archivo
        patterns = [
            # Modulo7_EduardoMoreno_01.jpg -> Eduardo Moreno
            r'[Mm][óo]?dulo?\s*\d+[_\s-]+([A-Za-zÀ-ÿ]+(?:[A-Z][a-z]+)?)',
            # Modulo_07_monserrathernandez_01.JPG -> monserrat hernandez
            r'[Mm][óo]?dulo?[_\s-]*\d+[_\s-]+([a-zA-ZÀ-ÿ]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Convertir CamelCase a espacio: EduardoMoreno -> Eduardo Moreno
                name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
                # Limpiar y capitalizar
                name = name.replace('_', ' ').replace('-', ' ').strip()
                name = ' '.join(word.capitalize() for word in name.split())
                return name
        return None
    
    def identify_student_from_file(self, file_data: Dict) -> Optional[Tuple[str, str]]:
        """Identifica estudiante del archivo usando múltiples estrategias."""
        try:
            filename = file_data.get('name', '')
            
            # LOG PARA DEBUG: Ver qué metadata llega realmente
            logger.debug(f"  📋 Analizando archivo: {filename}")
            logger.debug(f"  📋 Metadata disponible: lastModifyingUser={bool(file_data.get('lastModifyingUser'))}, owners={bool(file_data.get('owners'))}")
            
            # 1. Usuario que modificó por última vez (ACEPTAR TODOS LOS EMAILS)
            if 'lastModifyingUser' in file_data:
                user = file_data['lastModifyingUser']
                email = user.get('emailAddress', '')
                display_name = user.get('displayName', '')
                
                if email and '@' in email:  # ACEPTAR CUALQUIER EMAIL VÁLIDO
                    # Intentar extraer un mejor nombre del archivo si es posible
                    better_name = self._extract_name_from_filename(filename)
                    if better_name and len(better_name) > 3:
                        name = better_name
                    else:
                        name = display_name or email.split('@')[0]
                    
                    logger.info(f"  ✅ METADATA lastModifyingUser: {name} ({email})")
                    return (name, email)
            
            # 2. Propietario del archivo (ACEPTAR TODOS LOS EMAILS)
            if 'owners' in file_data and file_data['owners']:
                owner = file_data['owners'][0]
                email = owner.get('emailAddress', '')
                display_name = owner.get('displayName', '')
                
                if email and '@' in email:  # ACEPTAR CUALQUIER EMAIL VÁLIDO
                    # Intentar extraer un mejor nombre del archivo si es posible
                    better_name = self._extract_name_from_filename(filename)
                    if better_name and len(better_name) > 3:
                        name = better_name
                    else:
                        name = display_name or email.split('@')[0]
                    
                    logger.info(f"  ✅ METADATA owner: {name} ({email})")
                    return (name, email)
            
            # 3. Email en nombre del archivo
            email_match = re.search(self.email_pattern, filename)
            if email_match:
                email = email_match.group()
                name = email.split('@')[0]
                logger.debug(f"  👤 Email en filename: {name} ({email})")
                return (name, email)
            
            # 4. Patrones de nombre en el archivo - MEJORADOS CON ACENTOS
            name_patterns = [
                # NUEVO: Patrón para Módulo con acento: Módulo3_NombreApellido_01.jpg
                r'[Mm][óo]dulo?\s*\d+[_\s-]+([A-Za-zÀ-ÿ]{3,}[A-Za-zÀ-ÿ\s]*?)(?:[_\s-]+\d+)?\.?[a-zA-Z]*$',
                
                # Patrón específico: Modulo3_NombreApellido_01.jpg
                r'[Mm]odulo?\s*\d+[_\s-]+([A-Za-zÀ-ÿ]{3,}[A-Za-zÀ-ÿ\s]*?)(?:[_\s-]+\d+)?\.?[a-zA-Z]*$',
                
                # NUEVO: Patrón para nombres con múltiples guiones bajos: Modulo9_Luis_Francisco_Escoto_01.jpg
                r'[Mm][óo]?dulo?\s*\d+[_\s-]+([A-Za-zÀ-ÿ]+(?:[_\s][A-Za-zÀ-ÿ]+){1,3})(?:[_\s-]+\d+)?',
                
                # Patrón: Modulo 3_Nombre Apellido_01.png  
                r'[Mm][óo]?dulo?\s*\d+[_\s-]+([A-Za-zÀ-ÿ\s]{4,}?)(?:[_\s-]+\d+)?\.?[a-zA-Z]*$',
                
                # Patrón original: Nombre_Apellido o Nombre-Apellido
                r'^([A-Za-zÀ-ÿ]+[_\s-]+[A-Za-zÀ-ÿ]+)',  
                
                # Nombre seguido de separador
                r'^([A-Za-zÀ-ÿ\s]{3,}?)[-_\.]',         
                
                # Nombre seguido de número
                r'([A-Za-zÀ-ÿ\s]{3,}?)(?=\d)',          
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    name = match.group(1).replace('_', ' ').replace('-', ' ').strip()
                    
                    # Limpiar nombres específicos del patrón de módulo
                    name = re.sub(r'^[Mm][óo]?dulo?\s*\d+[_\s-]*', '', name, flags=re.IGNORECASE)
                    name = re.sub(r'[_\s-]*\d+[_\s-]*$', '', name)  # Quitar números al final
                    name = name.strip()
                    
                    # VALIDACIÓN MEJORADA: Evitar detectar "Módulo", "Modulo", "dulo" como nombres
                    palabras_invalidas = ['modulo', 'módulo', 'dulo', 'ejercicio', 'tarea', 'test']
                    
                    # Verificar que el nombre sea válido y NO sea una palabra prohibida
                    if (len(name) > 2 and 
                        not any(word == name.lower() for word in palabras_invalidas) and
                        not any(word in name.lower() for word in ['modulo', 'módulo', 'dulo']) and
                        name.lower() not in palabras_invalidas):
                        
                        # Limpiar caracteres especiales y normalizar espacios
                        name = ' '.join(name.split())  # Normalizar espacios múltiples
                        
                        # Si llegamos aquí sin metadata, es muy raro. Generar email temporal para evitar errores
                        logger.warning(f"  ⚠️ Nombre extraído sin metadata (raro): {name}")
                        email_name = name.lower().replace(' ', '.').replace('ñ', 'n').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                        email = f"{email_name}@extracted.temp"
                        return (name, email)
            
            logger.debug(f"  ❓ No identificado: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"  ❌ Error identificando estudiante: {e}")
            return None
    
    def sync_modules_to_db(self) -> Dict:
        """Sincroniza módulos de Google Drive con BD de forma adaptativa."""
        try:
            logger.info("🔄 Sincronizando módulos adaptativamente...")
            
            # Obtener módulos de Google Drive
            drive_modules = self.drive_client.list_folders_in_root()
            
            results = {
                'modules_processed': 0,
                'modules_created': 0,
                'modules_existing': 0,
                'errors': []
            }
            
            for module_folder in drive_modules:
                try:
                    module_name = module_folder['name']
                    drive_folder_id = module_folder['id']
                    
                    logger.info(f"  📚 Procesando: {module_name}")
                    
                    # Verificar si ya existe
                    existing_module = self.dao.get_module_by_drive_folder(drive_folder_id)
                    
                    if existing_module:
                        logger.debug(f"    ✅ Ya existe (ID: {existing_module['id']})")
                        results['modules_existing'] += 1
                    else:
                        # Crear nuevo módulo
                        try:
                            module_id = self.dao.create_module(
                                name=module_name,
                                drive_folder_id=drive_folder_id,
                                description=f"Módulo desde Google Drive: {module_name}"
                            )
                            logger.info(f"    ✅ Creado (ID: {module_id})")
                            results['modules_created'] += 1
                        except Exception as e:
                            logger.error(f"    ❌ Error creando módulo: {e}")
                            results['errors'].append(f"Error creando {module_name}: {e}")
                    
                    results['modules_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error procesando {module_folder.get('name', 'Unknown')}: {e}"
                    logger.error(f"  ❌ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"✅ Sync completo: {results['modules_created']} nuevos, {results['modules_existing']} existentes")
            return results
            
        except Exception as e:
            error_msg = f"Error en sincronización: {e}"
            logger.error(f"❌ {error_msg}")
            return {'error': error_msg, 'modules_processed': 0}
    
    def scan_module_smart(self, module_data: Dict) -> Dict:
        """
        Escanea un módulo de forma inteligente.
        module_data puede venir de BD o de Google Drive.
        """
        try:
            # Determinar si viene de BD o Drive
            if 'drive_folder_id' in module_data or 'folder_id' in module_data:
                # Viene de BD
                module_name = module_data['name']
                drive_folder_id = module_data.get('drive_folder_id') or module_data.get('folder_id')
                module_id = module_data['id']
                logger.info(f"🔍 Escaneando módulo de BD: {module_name}")
            else:
                # Viene de Google Drive
                module_name = module_data['name']
                drive_folder_id = module_data['id']
                
                # Buscar o crear en BD
                existing_module = self.dao.get_module_by_drive_folder(drive_folder_id)
                if existing_module:
                    module_id = existing_module['id']
                else:
                    module_id = self.dao.create_module(
                        name=module_name,
                        drive_folder_id=drive_folder_id,
                        description=f"Auto-creado durante escaneo: {module_name}"
                    )
                
                logger.info(f"🔍 Escaneando módulo de Drive: {module_name}")
            
            # Obtener archivos del módulo
            files = self.drive_client.list_files_in_folder(drive_folder_id, self.valid_mime_types)
            
            results = {
                'module_id': module_id,
                'module_name': module_name,
                'drive_folder_id': drive_folder_id,
                'files_found': len(files),
                'files_processed': 0,
                'students_created': 0,
                'submissions_created': 0,
                'submissions_updated': 0,
                'errors': []
            }
            
            logger.info(f"  📄 Archivos encontrados: {len(files)}")
            
            # Procesar cada archivo
            for i, file_data in enumerate(files, 1):
                try:
                    # Mostrar progreso cada 10 archivos o menos
                    if len(files) <= 50 or i % 10 == 0 or i == len(files):
                        logger.info(f"    📄 [{i}/{len(files)}] Procesando archivos...")
                    
                    logger.debug(f"    [{i}/{len(files)}] {file_data['name']}")
                    
                    # LOG DETALLADO DE METADATA (solo para los primeros 3 archivos para no saturar)
                    if i <= 3:
                        logger.info(f"    🔍 METADATA COMPLETA archivo {i}:")
                        logger.info(f"       - name: {file_data.get('name')}")
                        logger.info(f"       - lastModifyingUser: {file_data.get('lastModifyingUser')}")
                        logger.info(f"       - owners: {file_data.get('owners')}")
                    
                    # Identificar estudiante
                    student_info = self.identify_student_from_file(file_data)
                    if not student_info:
                        logger.warning(f"    ⚠️  Sin estudiante: {file_data['name']}")
                        continue
                    
                    student_name, student_email = student_info
                    logger.info(f"    ✅ DETECTADO: {student_name} → {file_data['name']}")
                    
                    # Crear/obtener estudiante
                    try:
                        student_id = self.dao.create_student(student_name, student_email)
                        
                        # Verificar si es nuevo
                        if self.dao.get_student_by_email(student_email):
                            logger.debug(f"      👤 Estudiante: {student_name}")
                        else:
                            logger.info(f"      ✅ Nuevo estudiante: {student_name}")
                            results['students_created'] += 1
                        
                    except Exception as e:
                        logger.error(f"      ❌ Error con estudiante {student_name}: {e}")
                        results['errors'].append(f"Error estudiante {student_name}: {e}")
                        continue
                    
                    # Crear submission
                    try:
                        submission_id = self.dao.create_submission(module_id, student_id, file_data)
                        results['submissions_created'] += 1
                        logger.debug(f"      📝 Submission: {submission_id}")
                        
                    except Exception as e:
                        logger.error(f"      ❌ Error submission {file_data['name']}: {e}")
                        results['errors'].append(f"Error submission {file_data['name']}: {e}")
                        continue
                    
                    results['files_processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error archivo {file_data.get('name', 'Unknown')}: {e}"
                    logger.error(f"    ❌ {error_msg}")
                    results['errors'].append(error_msg)
                    # También contar archivos con error como procesados
                    results['files_processed'] += 1
            
            logger.info(f"✅ Módulo [{module_name}] completado:")
            logger.info(f"  📁 Archivos: {results['files_processed']}/{results['files_found']} procesados")  
            logger.info(f"  👥 Estudiantes: {results['students_created']} nuevos")
            logger.info(f"  📝 Submissions: {results['submissions_created']} creadas")
            if results['errors']:
                logger.warning(f"  ⚠️  Errores: {len(results['errors'])}")
            return results
            
        except Exception as e:
            error_msg = f"Error escaneando módulo {module_data.get('name', 'Unknown')}: {e}"
            logger.error(f"❌ {error_msg}")
            return {'error': error_msg}
    
    def full_adaptive_scan(self) -> Dict:
        """Ejecuta escaneo completo adaptativo de todos los módulos."""
        try:
            logger.info("🚀 ESCANEO ADAPTATIVO COMPLETO")
            
            # Crear log de sync
            sync_id = self.dao.create_sync_log('full_adaptive_scan')
            
            # 1. Sincronizar módulos desde Drive
            logger.info("1️⃣ Sincronizando módulos...")
            sync_results = self.sync_modules_to_db()
            
            # 2. Obtener todos los módulos (ahora sincronizados)
            logger.info("2️⃣ Obteniendo módulos de BD...")
            modules = self.dao.get_all_modules()
            
            full_results = {
                'sync_id': sync_id,
                'sync_results': sync_results,
                'total_modules': len(modules),
                'modules_scanned': 0,
                'total_files': 0,
                'total_submissions': 0,
                'total_students': 0,
                'errors': sync_results.get('errors', []),
                'module_details': []
            }
            
            logger.info(f"3️⃣ Escaneando {len(modules)} módulos...")
            
            # 3. Escanear cada módulo
            for i, module in enumerate(modules, 1):
                try:
                    logger.info(f"📊 [{i}/{len(modules)}] {module['name']}")
                    
                    scan_result = self.scan_module_smart(module)
                    
                    if 'error' not in scan_result:
                        full_results['modules_scanned'] += 1
                        full_results['total_files'] += scan_result['files_found']
                        full_results['total_submissions'] += scan_result['submissions_created']
                        full_results['total_students'] += scan_result['students_created']
                        
                        full_results['module_details'].append({
                            'name': scan_result['module_name'],
                            'files': scan_result['files_found'],
                            'submissions': scan_result['submissions_created'],
                            'students': scan_result['students_created'],
                            'errors': len(scan_result['errors'])
                        })
                    else:
                        full_results['errors'].append(scan_result['error'])
                    
                except Exception as e:
                    error_msg = f"Error módulo {module.get('name', 'Unknown')}: {e}"
                    logger.error(f"  ❌ {error_msg}")
                    full_results['errors'].append(error_msg)
            
            # 4. Actualizar sync log
            status = 'completed' if not full_results['errors'] else 'completed_with_errors'
            self.dao.update_sync_log(
                sync_id=sync_id,
                status=status,
                files_processed=full_results['total_files'],
                errors=len(full_results['errors']),
                error_details=json.dumps({"errors": full_results['errors'][:3]}) if full_results['errors'] else None
            )
            
            # 5. Resumen final
            logger.info("=" * 70)
            logger.info("🎉 ESCANEO ADAPTATIVO COMPLETADO")
            logger.info(f"  📊 Módulos: {full_results['modules_scanned']}/{full_results['total_modules']}")
            logger.info(f"  📄 Archivos: {full_results['total_files']}")
            logger.info(f"  📝 Submissions: {full_results['total_submissions']}")
            logger.info(f"  👥 Estudiantes nuevos: {full_results['total_students']}")
            if full_results['errors']:
                logger.warning(f"  ⚠️  Errores: {len(full_results['errors'])}")
                for error in full_results['errors'][:3]:
                    logger.warning(f"    • {error}")
                if len(full_results['errors']) > 3:
                    logger.warning(f"    ... y {len(full_results['errors']) - 3} más")
            logger.info("=" * 70)
            
            return full_results
            
        except Exception as e:
            error_msg = f"Error en escaneo completo: {e}"
            logger.error(f"❌ {error_msg}")
            
            if 'sync_id' in locals():
                error_json = json.dumps({"error": error_msg, "timestamp": datetime.now().isoformat()})
                self.dao.update_sync_log(sync_id=sync_id, status='failed', error_details=error_json)
            
            return {'error': error_msg}


# Función de prueba
def test_adaptive_scanner():
    try:
        logger.info("🧪 PROBANDO SCANNER ADAPTATIVO")
        
        scanner = AdaptiveModuleScanner()
        
        # Mostrar estadísticas iniciales
        logger.info("📊 Estadísticas iniciales:")
        stats = scanner.dao.get_statistics()
        for key, value in stats.items():
            logger.info(f"  • {key}: {value}")
        
        # Ejecutar escaneo completo
        results = scanner.full_adaptive_scan()
        
        # Mostrar estadísticas finales
        logger.info("📊 Estadísticas finales:")
        final_stats = scanner.dao.get_statistics()
        for key, value in final_stats.items():
            logger.info(f"  • {key}: {value}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_adaptive_scanner()