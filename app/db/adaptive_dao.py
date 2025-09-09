import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Optional, Any
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class AdaptiveDatabaseDAO:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Cache para estructuras de tablas
        self.table_schemas = {}
        self._discover_schema()
    
    def _discover_schema(self):
        """Descubre automáticamente la estructura de todas las tablas."""
        try:
            logger.info("🔍 Descubriendo estructura de la base de datos...")
            
            with self.get_cursor() as cur:
                # Obtener todas las tablas
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                
                tables = [row['table_name'] for row in cur.fetchall()]
                logger.info(f"📊 Tablas encontradas: {', '.join(tables)}")
                
                # Obtener estructura de cada tabla
                for table_name in tables:
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position;
                    """, (table_name,))
                    
                    columns = cur.fetchall()
                    self.table_schemas[table_name] = {
                        'columns': {col['column_name']: col for col in columns},
                        'column_names': [col['column_name'] for col in columns]
                    }
                    
                    logger.info(f"  📋 {table_name}: {len(columns)} columnas")
                    for col in columns[:3]:  # Mostrar primeras 3 columnas
                        logger.debug(f"    • {col['column_name']} ({col['data_type']})")
                    if len(columns) > 3:
                        logger.debug(f"    ... y {len(columns) - 3} más")
        
        except Exception as e:
            logger.error(f"❌ Error descubriendo schema: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
            finally:
                cur.close()
    
    def _build_insert_query(self, table_name: str, data: Dict) -> tuple:
        """Construye automáticamente query INSERT basado en la estructura real."""
        if table_name not in self.table_schemas:
            raise ValueError(f"Tabla {table_name} no encontrada en schema")
        
        available_columns = self.table_schemas[table_name]['column_names']
        
        # Filtrar solo las columnas que existen y tienen datos
        insert_columns = []
        insert_values = []
        placeholders = []
        
        for column, value in data.items():
            if column in available_columns and value is not None:
                insert_columns.append(column)
                insert_values.append(value)
                placeholders.append('%s')
        
        if not insert_columns:
            raise ValueError(f"No hay columnas válidas para insertar en {table_name}")
        
        query = f"""
            INSERT INTO {table_name} ({', '.join(insert_columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING id
        """
        
        return query, insert_values
    
    # MODULES - Adaptativo
    def get_all_modules(self) -> List[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM modules ORDER BY name")
            return cur.fetchall()
    
    def get_module_by_id(self, module_id: str) -> Optional[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM modules WHERE id = %s", (module_id,))
            return cur.fetchone()
    
    def get_module_by_drive_folder(self, drive_folder_id: str) -> Optional[Dict]:
        """Busca módulo por drive folder ID."""
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM modules WHERE drive_folder_id = %s", (drive_folder_id,))
            return cur.fetchone()
    
    def _generate_module_code(self, name: str) -> str:
        """Genera código único para el módulo basado en su nombre."""
        import re
        
        # Extraer número del módulo si existe
        module_match = re.search(r'[Mm]odulo?\s*(\d+)', name)
        if module_match:
            module_num = module_match.group(1).zfill(2)
            return f"MOD{module_num}"
        
        # Para módulos especiales, generar código basado en nombre
        special_codes = {
            'correcciones': 'CORR',
            'dibujos': 'DRAW',
            'lives': 'LIVE',
            'evaluacion': 'EVAL',
            'autoevaluacion': 'AUTO',
            'examen': 'EXAM',
            'tarea': 'TASK'
        }
        
        name_lower = name.lower()
        for keyword, code in special_codes.items():
            if keyword in name_lower:
                return code
        
        # Código genérico basado en primeras 4 letras
        clean_name = re.sub(r'[^A-Za-z]', '', name)
        return clean_name[:4].upper() or 'MOD0'
    
    def create_module(self, name: str, drive_folder_id: str, description: str = None) -> str:
        """Crea módulo adaptándose a la estructura real."""
        # Generar código basado en el nombre del módulo
        code = self._generate_module_code(name)
        
        # Generar order_index basado en el número de módulos existentes
        with self.get_cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(order_index), 0) + 1 as next_order FROM modules")
            result = cur.fetchone()
            next_order = result['next_order']
        
        module_data = {
            'name': name,
            'description': description,
            'code': code,  # Campo requerido
            'drive_folder_id': drive_folder_id,  # Campo requerido
            'order_index': next_order,  # Campo requerido
            'drive_folder_url': f"https://drive.google.com/drive/folders/{drive_folder_id}"
        }
        
        query, values = self._build_insert_query('modules', module_data)
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
            result = cur.fetchone()
            return result['id']
    
    # STUDENTS - Adaptativo
    def get_all_students(self) -> List[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM students ORDER BY full_name")
            return cur.fetchall()
    
    def get_student_by_email(self, email: str) -> Optional[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM students WHERE email = %s", (email,))
            return cur.fetchone()
    
    def create_student(self, name: str, email: str) -> str:
        """Crea estudiante con ON CONFLICT automático."""
        student_data = {
            'full_name': name,  # Campo correcto según schema
            'email': email
        }
        
        # Construir query con ON CONFLICT si existe la columna email Y el email es válido
        student_columns = self.table_schemas.get('students', {}).get('column_names', [])
        
        # Usar ON CONFLICT para emails válidos (evita duplicados)
        if 'email' in student_columns and email and "@" in email:
            query, values = self._build_insert_query('students', student_data)
            query = query.replace('RETURNING id', '''
                ON CONFLICT (email) DO UPDATE 
                SET full_name = EXCLUDED.full_name, updated_at = NOW()
                RETURNING id
            ''')
        else:
            # Sin email válido, crear sin conflict resolution
            query, values = self._build_insert_query('students', student_data)
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
            result = cur.fetchone()
            return result['id']
    
    # SUBMISSIONS - Completamente adaptativo
    def create_submission(self, module_id: str, student_id: str, file_data: Dict) -> str:
        """
        Crea submission mapeando automáticamente los datos del archivo.
        file_data viene de Google Drive API.
        """
        logger.debug(f"📝 Creando submission para archivo: {file_data.get('name', 'Unknown')}")
        
        # Mapeo automático de datos de Google Drive a columnas de BD
        submission_data = {}
        
        # Campos básicos
        submission_data['module_id'] = module_id
        submission_data['student_id'] = student_id
        
        # Mapear datos del archivo de Google Drive
        drive_mapping = {
            'file_id': file_data.get('id'),
            'filename': file_data.get('name'),
            'mime_type': file_data.get('mimeType'),
            'size_bytes': int(file_data.get('size', 0)),
            'drive_url': f"https://drive.google.com/file/d/{file_data.get('id')}/view",
            'created_time': self._parse_drive_timestamp(file_data.get('createdTime')),
            'modified_time': self._parse_drive_timestamp(file_data.get('modifiedTime')),
            'detected_at': datetime.now()
        }
        
        # Extraer información del usuario
        if 'lastModifyingUser' in file_data:
            user = file_data['lastModifyingUser']
            drive_mapping['uploaded_by_email'] = user.get('emailAddress')
        
        if 'owners' in file_data and file_data['owners']:
            owner = file_data['owners'][0]
            drive_mapping['owner_email'] = owner.get('emailAddress')
        
        # Calcular campos derivados
        if drive_mapping['size_bytes']:
            drive_mapping['size_mb'] = round(drive_mapping['size_bytes'] / (1024 * 1024), 2)
        
        if drive_mapping['filename']:
            # Manejar archivos sin extensión o con extensiones largas
            if '.' in drive_mapping['filename']:
                extension = drive_mapping['filename'].split('.')[-1].lower()
                # Limitar a 50 caracteres (nuevo límite del campo)
                drive_mapping['file_extension'] = extension[:50] if extension else 'unknown'
            else:
                drive_mapping['file_extension'] = 'noext'  # Sin extensión
            
            # DEBUG: Log si la extensión es muy larga
            if len(drive_mapping.get('file_extension', '')) > 20:
                logger.warning(f"⚠️ Extensión larga detectada: {drive_mapping['file_extension']} ({len(drive_mapping['file_extension'])} chars) en archivo: {drive_mapping['filename']}")
        
        # Solo incluir campos que existen en la tabla
        submission_columns = self.table_schemas.get('submissions', {}).get('column_names', [])
        for key, value in drive_mapping.items():
            if key in submission_columns:
                submission_data[key] = value
        
        # Construir query con ON CONFLICT para file_id
        query, values = self._build_insert_query('submissions', submission_data)
        
        if 'file_id' in submission_columns:
            query = query.replace('RETURNING id', '''
                ON CONFLICT (file_id) DO UPDATE 
                SET filename = EXCLUDED.filename,
                    size_bytes = EXCLUDED.size_bytes,
                    modified_time = EXCLUDED.modified_time,
                    detected_at = NOW()
                RETURNING id
            ''')
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
            result = cur.fetchone()
            logger.debug(f"  ✅ Submission creada/actualizada (ID: {result['id']})")
            return result['id']
    
    def _parse_drive_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parsea timestamp de Google Drive."""
        if not timestamp_str:
            return None
        
        try:
            from dateutil.parser import parse as parse_date
            return parse_date(timestamp_str).replace(tzinfo=None)
        except Exception as e:
            logger.debug(f"Error parseando timestamp {timestamp_str}: {e}")
            return None
    
    # SYNC LOGS
    def create_sync_log(self, sync_type: str = 'manual') -> str:
        sync_data = {
            'sync_type': sync_type,
            'status': 'running',
            'started_at': datetime.now()
        }
        
        query, values = self._build_insert_query('sync_logs', sync_data)
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
            result = cur.fetchone()
            return result['id']
    
    def update_sync_log(self, sync_id: str, status: str, **kwargs):
        """Actualiza sync log con campos que existen."""
        sync_columns = self.table_schemas.get('sync_logs', {}).get('column_names', [])
        
        update_fields = ['status = %s']
        values = [status]
        
        # Campos opcionales que podrían existir
        optional_fields = {
            'files_processed': kwargs.get('files_processed'),
            'errors': kwargs.get('errors'),
            'error_details': kwargs.get('error_details'),
            'completed_at': datetime.now() if status in ['completed', 'failed'] else None
        }
        
        for field, value in optional_fields.items():
            if field in sync_columns and value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)
        
        values.append(sync_id)
        
        query = f"""
            UPDATE sync_logs 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
    
    # ESTADÍSTICAS ADAPTATIVAS
    def get_statistics(self) -> Dict:
        """Genera estadísticas basándose en las tablas y columnas reales."""
        with self.get_cursor() as cur:
            stats = {}
            
            # Conteos básicos
            if 'students' in self.table_schemas:
                cur.execute("SELECT COUNT(*) as count FROM students")
                stats['total_students'] = cur.fetchone()['count']
            
            if 'modules' in self.table_schemas:
                cur.execute("SELECT COUNT(*) as count FROM modules")
                stats['total_modules'] = cur.fetchone()['count']
            
            if 'submissions' in self.table_schemas:
                cur.execute("SELECT COUNT(*) as count FROM submissions")
                stats['total_submissions'] = cur.fetchone()['count']
                
                # Actividad reciente si existe columna de tiempo
                submission_cols = self.table_schemas['submissions']['column_names']
                time_columns = [col for col in ['detected_at', 'modified_time', 'created_time'] 
                               if col in submission_cols]
                
                if time_columns:
                    time_col = time_columns[0]  # Usar la primera columna de tiempo disponible
                    
                    cur.execute(f"""
                        SELECT COUNT(*) as count 
                        FROM submissions 
                        WHERE {time_col} > NOW() - INTERVAL '7 days'
                    """)
                    stats['submissions_last_week'] = cur.fetchone()['count']
                    
                    cur.execute(f"""
                        SELECT COUNT(DISTINCT student_id) as count 
                        FROM submissions 
                        WHERE {time_col} > NOW() - INTERVAL '30 days'
                    """)
                    stats['active_students_last_month'] = cur.fetchone()['count']
            
            return stats
    
    def test_connection(self) -> bool:
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_schema_info(self) -> Dict:
        """Retorna información completa del schema descubierto."""
        return {
            'tables': list(self.table_schemas.keys()),
            'schemas': self.table_schemas
        }


# Instancia singleton
adaptive_dao = AdaptiveDatabaseDAO()