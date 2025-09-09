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


class DatabaseDAO:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")
    
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
    
    # MODULES
    def get_all_modules(self) -> List[Dict]:
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM modules 
                ORDER BY name
            """)
            return cur.fetchall()
    
    def get_module_by_id(self, module_id: int) -> Optional[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM modules WHERE id = %s", (module_id,))
            return cur.fetchone()
    
    def create_module(self, name: str, drive_folder_id: str, description: str = None) -> int:
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO modules (name, drive_folder_id, description)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (name, drive_folder_id, description))
            return cur.fetchone()['id']
    
    def update_module_last_scan(self, module_id: int):
        with self.get_cursor() as cur:
            cur.execute("""
                UPDATE modules 
                SET last_scanned_at = %s 
                WHERE id = %s
            """, (datetime.now(), module_id))
    
    # STUDENTS
    def get_all_students(self, active_only: bool = True) -> List[Dict]:
        query = "SELECT * FROM students ORDER BY name"
        
        with self.get_cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    
    def get_student_by_email(self, email: str) -> Optional[Dict]:
        with self.get_cursor() as cur:
            cur.execute("SELECT * FROM students WHERE email = %s", (email,))
            return cur.fetchone()
    
    def create_student(self, name: str, email: str) -> int:
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO students (name, email)
                VALUES (%s, %s)
                ON CONFLICT (email) DO UPDATE
                SET name = EXCLUDED.name
                RETURNING id
            """, (name, email))
            return cur.fetchone()['id']
    
    # SUBMISSIONS
    def create_submission(self, module_id: int, student_id: int, 
                         file_name: str, drive_file_id: str,
                         file_size: int, mime_type: str,
                         submitted_at: datetime = None) -> int:
        if submitted_at is None:
            submitted_at = datetime.now()
        
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO submissions 
                (module_id, student_id, file_name, drive_file_id, 
                 file_size, mime_type, submitted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (drive_file_id) DO UPDATE
                SET file_name = EXCLUDED.file_name,
                    file_size = EXCLUDED.file_size,
                    submitted_at = EXCLUDED.submitted_at
                RETURNING id
            """, (module_id, student_id, file_name, drive_file_id,
                  file_size, mime_type, submitted_at))
            return cur.fetchone()['id']
    
    def get_submissions_by_module(self, module_id: int) -> List[Dict]:
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT s.*, st.name as student_name, st.email as student_email
                FROM submissions s
                JOIN students st ON s.student_id = st.id
                WHERE s.module_id = %s
                ORDER BY s.submitted_at DESC
            """, (module_id,))
            return cur.fetchall()
    
    def get_submissions_by_student(self, student_id: int) -> List[Dict]:
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT s.*, m.name as module_name
                FROM submissions s
                JOIN modules m ON s.module_id = m.id
                WHERE s.student_id = %s
                ORDER BY s.submitted_at DESC
            """, (student_id,))
            return cur.fetchall()
    
    # SYNC LOGS
    def create_sync_log(self, sync_type: str = 'manual') -> int:
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO sync_logs (sync_type, status, started_at)
                VALUES (%s, 'running', %s)
                RETURNING id
            """, (sync_type, datetime.now()))
            return cur.fetchone()['id']
    
    def update_sync_log(self, sync_id: int, status: str, 
                       files_processed: int = 0, errors: int = 0,
                       error_details: str = None):
        with self.get_cursor() as cur:
            cur.execute("""
                UPDATE sync_logs
                SET status = %s,
                    files_processed = %s,
                    errors = %s,
                    error_details = %s,
                    completed_at = CASE 
                        WHEN %s IN ('completed', 'failed') THEN %s 
                        ELSE completed_at 
                    END
                WHERE id = %s
            """, (status, files_processed, errors, error_details,
                  status, datetime.now(), sync_id))
    
    # METRICS
    def update_daily_metrics(self, date: datetime = None):
        if date is None:
            date = datetime.now().date()
        
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO metrics_daily (date, total_students, total_modules, 
                                         total_submissions, active_students)
                SELECT %s,
                       (SELECT COUNT(*) FROM students),
                       (SELECT COUNT(*) FROM modules),
                       (SELECT COUNT(*) FROM submissions WHERE DATE(submitted_at) = %s),
                       (SELECT COUNT(DISTINCT student_id) FROM submissions 
                        WHERE DATE(submitted_at) = %s)
                ON CONFLICT (date) DO UPDATE
                SET total_students = EXCLUDED.total_students,
                    total_modules = EXCLUDED.total_modules,
                    total_submissions = EXCLUDED.total_submissions,
                    active_students = EXCLUDED.active_students,
                    updated_at = NOW()
            """, (date, date, date))
    
    def update_module_metrics(self, module_id: int):
        with self.get_cursor() as cur:
            cur.execute("""
                INSERT INTO metrics_module_summary (module_id, total_submissions,
                                                   unique_students, avg_file_size,
                                                   last_submission_at)
                SELECT %s,
                       COUNT(*),
                       COUNT(DISTINCT student_id),
                       AVG(file_size),
                       MAX(submitted_at)
                FROM submissions
                WHERE module_id = %s
                ON CONFLICT (module_id) DO UPDATE
                SET total_submissions = EXCLUDED.total_submissions,
                    unique_students = EXCLUDED.unique_students,
                    avg_file_size = EXCLUDED.avg_file_size,
                    last_submission_at = EXCLUDED.last_submission_at,
                    updated_at = NOW()
            """, (module_id, module_id))
    
    # REPORT PREFERENCES
    def get_report_preferences(self) -> Dict:
        with self.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM report_preferences 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = cur.fetchone()
            if not result:
                # Crear configuración por defecto
                cur.execute("""
                    INSERT INTO report_preferences 
                    (recipient_emails, frequency_days, include_charts, 
                     include_summary, format_types)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (['jean@academia.com'], 15, True, True, ['excel', 'pdf']))
                result = cur.fetchone()
            return result
    
    def update_report_preferences(self, **kwargs):
        allowed_fields = ['recipient_emails', 'frequency_days', 
                         'include_charts', 'include_summary', 'format_types']
        
        fields_to_update = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                fields_to_update.append(f"{field} = %s")
                values.append(kwargs[field])
        
        if not fields_to_update:
            return
        
        query = f"""
            UPDATE report_preferences 
            SET {', '.join(fields_to_update)}, updated_at = NOW()
            WHERE id = (SELECT id FROM report_preferences ORDER BY created_at DESC LIMIT 1)
        """
        
        with self.get_cursor() as cur:
            cur.execute(query, values)
    
    # UTILITY METHODS
    def get_statistics(self) -> Dict:
        with self.get_cursor() as cur:
            stats = {}
            
            # Total counts
            cur.execute("SELECT COUNT(*) as count FROM students")
            stats['total_students'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM modules")
            stats['total_modules'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM submissions")
            stats['total_submissions'] = cur.fetchone()['count']
            
            # Recent activity
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM submissions 
                WHERE submitted_at > NOW() - INTERVAL '7 days'
            """)
            stats['submissions_last_week'] = cur.fetchone()['count']
            
            cur.execute("""
                SELECT COUNT(DISTINCT student_id) as count 
                FROM submissions 
                WHERE submitted_at > NOW() - INTERVAL '30 days'
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


# Singleton instance
dao = DatabaseDAO()