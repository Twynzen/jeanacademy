import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GoogleDriveClient:
    def __init__(self):
        self.service = None
        self.root_folder_id = os.getenv('DRIVE_FOLDER_ID')
        self.service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_PATH')
        
        if not self.root_folder_id:
            error_msg = "❌ DRIVE_FOLDER_ID no configurado en .env"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not self.service_account_file:
            error_msg = "❌ GOOGLE_SERVICE_ACCOUNT_JSON_PATH no configurado en .env"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"📁 Folder ID configurado: {self.root_folder_id}")
        logger.info(f"🔑 Service Account: {self.service_account_file}")
        
        self._authenticate()
    
    def _authenticate(self):
        try:
            logger.info("🔐 Autenticando con Google Drive...")
            
            # Verificar que el archivo existe
            if not os.path.exists(self.service_account_file):
                error_msg = f"❌ Archivo de credenciales no encontrado: {self.service_account_file}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            # Autenticar con service account
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("✅ Autenticación exitosa con Google Drive")
            
            # Verificar acceso a la carpeta raíz
            self._verify_folder_access()
            
        except Exception as e:
            error_msg = f"❌ Error al autenticar con Google Drive: {str(e)}"
            logger.error(error_msg)
            raise
    
    def _verify_folder_access(self):
        try:
            logger.info(f"🔍 Verificando acceso a carpeta: {self.root_folder_id}")
            
            result = self.service.files().get(
                fileId=self.root_folder_id,
                fields='id, name, mimeType'
            ).execute()
            
            logger.info(f"✅ Acceso confirmado a carpeta: {result.get('name', 'Sin nombre')}")
            
            if result.get('mimeType') != 'application/vnd.google-apps.folder':
                error_msg = f"❌ El ID proporcionado no es una carpeta: {self.root_folder_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
        except HttpError as e:
            if e.resp.status == 404:
                error_msg = f"❌ Carpeta no encontrada o sin permisos: {self.root_folder_id}"
                logger.error(error_msg)
                logger.error("⚠️  Verifica que la carpeta esté compartida con el Service Account")
            else:
                error_msg = f"❌ Error HTTP al verificar carpeta: {e}"
                logger.error(error_msg)
            raise
    
    def list_folders_in_root(self) -> List[Dict]:
        try:
            logger.info(f"📂 Listando carpetas en: {self.root_folder_id}")
            
            query = f"'{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, createdTime, modifiedTime)",
                pageSize=100
            ).execute()
            
            folders = results.get('files', [])
            logger.info(f"✅ Encontradas {len(folders)} carpetas (módulos)")
            
            for folder in folders:
                logger.debug(f"  📁 {folder['name']} (ID: {folder['id']})")
            
            return folders
            
        except HttpError as e:
            error_msg = f"❌ Error al listar carpetas: {e}"
            logger.error(error_msg)
            raise
    
    def list_files_in_folder(self, folder_id: str, mime_types: List[str] = None) -> List[Dict]:
        try:
            logger.info(f"🔍 Listando archivos en carpeta: {folder_id}")
            
            # Construir query
            query = f"'{folder_id}' in parents and trashed=false"
            
            # Filtrar por tipos MIME si se especifican
            if mime_types:
                mime_queries = [f"mimeType='{mt}'" for mt in mime_types]
                query += f" and ({' or '.join(mime_queries)})"
                logger.debug(f"  Filtrando por tipos: {mime_types}")
            
            all_files = []
            page_token = None
            
            while True:
                results = self.service.files().list(
                    q=query,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, lastModifyingUser, owners, parents)",
                    pageSize=100,
                    pageToken=page_token
                ).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"✅ Encontrados {len(all_files)} archivos")
            
            for file in all_files[:5]:  # Log primeros 5 archivos
                logger.debug(f"  📄 {file['name']} ({file.get('mimeType', 'Unknown')})")
            
            if len(all_files) > 5:
                logger.debug(f"  ... y {len(all_files) - 5} archivos más")
            
            return all_files
            
        except HttpError as e:
            error_msg = f"❌ Error al listar archivos en carpeta {folder_id}: {e}"
            logger.error(error_msg)
            raise
    
    def get_file_metadata(self, file_id: str) -> Dict:
        try:
            logger.debug(f"📋 Obteniendo metadata de archivo: {file_id}")
            
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, lastModifyingUser, owners, parents, webViewLink"
            ).execute()
            
            logger.debug(f"✅ Metadata obtenida para: {file.get('name', 'Unknown')}")
            return file
            
        except HttpError as e:
            error_msg = f"❌ Error al obtener metadata del archivo {file_id}: {e}"
            logger.error(error_msg)
            raise
    
    def scan_all_modules(self) -> Dict[str, List[Dict]]:
        try:
            logger.info("🚀 Iniciando escaneo completo de módulos...")
            
            # Obtener todas las carpetas (módulos)
            modules = self.list_folders_in_root()
            
            if not modules:
                logger.warning("⚠️  No se encontraron módulos en la carpeta raíz")
                return {}
            
            results = {}
            mime_types_imagenes = [
                'image/jpeg',
                'image/jpg', 
                'image/png',
                'image/gif',
                'image/bmp'
            ]
            
            # Escanear cada módulo
            for i, module in enumerate(modules, 1):
                module_name = module['name']
                module_id = module['id']
                
                logger.info(f"📊 [{i}/{len(modules)}] Escaneando módulo: {module_name}")
                
                try:
                    # Obtener archivos del módulo
                    files = self.list_files_in_folder(module_id, mime_types_imagenes)
                    
                    results[module_name] = {
                        'module_id': module_id,
                        'module_name': module_name,
                        'files': files,
                        'total_files': len(files),
                        'scanned_at': datetime.now().isoformat()
                    }
                    
                    logger.info(f"  ✅ {len(files)} archivos encontrados en {module_name}")
                    
                except Exception as e:
                    logger.error(f"  ❌ Error escaneando módulo {module_name}: {e}")
                    results[module_name] = {
                        'module_id': module_id,
                        'module_name': module_name,
                        'error': str(e),
                        'files': [],
                        'total_files': 0,
                        'scanned_at': datetime.now().isoformat()
                    }
            
            # Resumen final
            total_modules = len(results)
            total_files = sum(r['total_files'] for r in results.values())
            modules_with_errors = sum(1 for r in results.values() if 'error' in r)
            
            logger.info("=" * 50)
            logger.info("📈 RESUMEN DEL ESCANEO:")
            logger.info(f"  • Módulos escaneados: {total_modules}")
            logger.info(f"  • Total de archivos: {total_files}")
            if modules_with_errors:
                logger.warning(f"  • Módulos con errores: {modules_with_errors}")
            logger.info("=" * 50)
            
            return results
            
        except Exception as e:
            error_msg = f"❌ Error durante el escaneo completo: {e}"
            logger.error(error_msg)
            raise
    
    def test_connection(self) -> bool:
        try:
            logger.info("🧪 Probando conexión con Google Drive...")
            
            # Intentar obtener información sobre la carpeta raíz
            result = self.service.files().get(
                fileId=self.root_folder_id,
                fields='id, name'
            ).execute()
            
            logger.info(f"✅ Conexión exitosa. Carpeta: {result.get('name', 'Sin nombre')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallo en la prueba de conexión: {e}")
            return False


# Función de prueba rápida
def test_drive_connection():
    try:
        client = GoogleDriveClient()
        if client.test_connection():
            logger.info("✅ Cliente de Google Drive configurado correctamente")
            
            # Listar módulos disponibles
            modules = client.list_folders_in_root()
            logger.info(f"📚 Módulos disponibles: {len(modules)}")
            for module in modules[:5]:
                logger.info(f"  • {module['name']}")
            
            return True
    except Exception as e:
        logger.error(f"❌ Error al configurar cliente: {e}")
        return False


if __name__ == "__main__":
    test_drive_connection()