"""
Database migration manager for handling schema changes and data migrations
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sqlite3
import shutil

# Import database components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.configuration_manager import config_manager
from services.database_manager import database_manager
from models.database_models import db

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations and schema changes"""
    
    def __init__(self):
        self.db_manager = database_manager
        self.migrations_dir = Path(__file__).parent
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_database(self) -> Path:
        """Create a backup of the current database"""
        try:
            db_url = config_manager.get_database_url()
            
            if db_url.startswith('sqlite:///'):
                # SQLite backup
                db_path = Path(db_url.replace('sqlite:///', ''))
                
                if not db_path.exists():
                    logger.warning(f"Database file {db_path} does not exist")
                    return None
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.backup_dir / f"attendance_backup_{timestamp}.db"
                
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                return backup_path
            else:
                logger.warning("Database backup only supported for SQLite currently")
                return None
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            raise
    
    def restore_database(self, backup_path: Path) -> bool:
        """Restore database from backup"""
        try:
            db_url = config_manager.get_database_url()
            
            if db_url.startswith('sqlite:///'):
                db_path = Path(db_url.replace('sqlite:///', ''))
                
                if not backup_path.exists():
                    logger.error(f"Backup file {backup_path} does not exist")
                    return False
                
                # Create backup of current database before restore
                if db_path.exists():
                    current_backup = self.backup_database()
                    logger.info(f"Current database backed up to {current_backup}")
                
                shutil.copy2(backup_path, db_path)
                logger.info(f"Database restored from {backup_path}")
                return True
            else:
                logger.error("Database restore only supported for SQLite currently")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def check_legacy_data(self) -> Dict[str, Any]:
        """Check for legacy data that needs migration"""
        try:
            db_url = config_manager.get_database_url()
            
            if not db_url.startswith('sqlite:///'):
                logger.warning("Legacy data check only supported for SQLite")
                return {}
            
            db_path = db_url.replace('sqlite:///', '')
            
            if not Path(db_path).exists():
                logger.info("No existing database found")
                return {}
            
            # Connect directly to check legacy tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if legacy 'add' table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='add'")
            legacy_table_exists = cursor.fetchone() is not None
            
            legacy_data = {}
            
            if legacy_table_exists:
                cursor.execute("SELECT COUNT(*) FROM 'add'")
                legacy_count = cursor.fetchone()[0]
                legacy_data['legacy_records'] = legacy_count
                
                # Get sample data
                cursor.execute("SELECT classname, coordinator, stuname FROM 'add' LIMIT 5")
                sample_data = cursor.fetchall()
                legacy_data['sample_data'] = sample_data
            
            # Check if new tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
            new_tables_exist = cursor.fetchone() is not None
            legacy_data['new_schema_exists'] = new_tables_exist
            
            conn.close()
            
            return legacy_data
            
        except Exception as e:
            logger.error(f"Failed to check legacy data: {e}")
            return {}
    
    def migrate_to_new_schema(self) -> bool:
        """Migrate from legacy schema to new schema"""
        try:
            logger.info("Starting migration to new schema...")
            
            # Create backup first
            backup_path = self.backup_database()
            if backup_path:
                logger.info(f"Backup created: {backup_path}")
            
            # Check legacy data
            legacy_info = self.check_legacy_data()
            
            if not legacy_info.get('legacy_records', 0):
                logger.info("No legacy data to migrate")
            else:
                logger.info(f"Found {legacy_info['legacy_records']} legacy records to migrate")
            
            # Create new tables
            logger.info("Creating new database schema...")
            self.db_manager.create_tables()
            
            # Migrate legacy data if it exists
            if legacy_info.get('legacy_records', 0) > 0:
                logger.info("Migrating legacy data...")
                self.db_manager.migrate_legacy_data()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            
            # Attempt to restore from backup
            if backup_path and backup_path.exists():
                logger.info("Attempting to restore from backup...")
                if self.restore_database(backup_path):
                    logger.info("Database restored from backup")
                else:
                    logger.error("Failed to restore from backup")
            
            return False
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful"""
        try:
            verification_results = {}
            
            # Check database health
            verification_results['database_healthy'] = self.db_manager.health_check()
            
            # Check table existence
            with self.db_manager.get_session() as session:
                # Try to query new tables
                try:
                    from models.database_models import Student, Class, AttendanceRecord
                    
                    student_count = session.query(Student).count()
                    class_count = session.query(Class).count()
                    record_count = session.query(AttendanceRecord).count()
                    
                    verification_results['students_count'] = student_count
                    verification_results['classes_count'] = class_count
                    verification_results['records_count'] = record_count
                    verification_results['tables_accessible'] = True
                    
                except Exception as e:
                    verification_results['tables_accessible'] = False
                    verification_results['table_error'] = str(e)
            
            # Check legacy data
            legacy_info = self.check_legacy_data()
            verification_results['legacy_data'] = legacy_info
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return {'error': str(e)}
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            status = {}
            
            # Check if database exists
            db_url = config_manager.get_database_url()
            if db_url.startswith('sqlite:///'):
                db_path = Path(db_url.replace('sqlite:///', ''))
                status['database_exists'] = db_path.exists()
            else:
                status['database_exists'] = self.db_manager.health_check()
            
            # Check legacy data
            legacy_info = self.check_legacy_data()
            status['legacy_data'] = legacy_info
            
            # Check new schema
            status['new_schema_ready'] = legacy_info.get('new_schema_exists', False)
            
            # Determine migration needed
            has_legacy = legacy_info.get('legacy_records', 0) > 0
            has_new_schema = legacy_info.get('new_schema_exists', False)
            
            if not status['database_exists']:
                status['migration_needed'] = 'create_new'
            elif has_legacy and not has_new_schema:
                status['migration_needed'] = 'migrate_legacy'
            elif not has_legacy and not has_new_schema:
                status['migration_needed'] = 'create_new'
            else:
                status['migration_needed'] = 'none'
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {'error': str(e)}


# Global migration manager instance
migration_manager = MigrationManager()