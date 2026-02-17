"""
Simplified Database Manager for the attendance system
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import sqlite3
from pathlib import Path

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.configuration_manager import config_manager

logger = logging.getLogger(__name__)


class SimpleDatabaseManager:
    """Simplified database manager for basic operations"""
    
    def __init__(self):
        self.db_url = config_manager.get_database_url()
        self.db_path = self.db_url.replace('sqlite:///', '') if self.db_url.startswith('sqlite:///') else None
    
    def get_connection(self):
        """Get database connection"""
        if not self.db_path:
            raise ValueError("Only SQLite databases are supported")
        
        return sqlite3.connect(self.db_path)
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def create_tables(self):
        """Create database tables using Flask-SQLAlchemy"""
        try:
            # Import here to avoid circular imports
            from attendance import app, db
            
            with app.app_context():
                db.create_all()
                logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def check_legacy_data(self) -> Dict[str, Any]:
        """Check for legacy data that needs migration"""
        try:
            if not self.db_path or not Path(self.db_path).exists():
                return {'legacy_records': 0, 'new_schema_exists': False}
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if legacy 'add' table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='add'")
                legacy_table_exists = cursor.fetchone() is not None
                
                legacy_count = 0
                if legacy_table_exists:
                    cursor.execute("SELECT COUNT(*) FROM 'add'")
                    legacy_count = cursor.fetchone()[0]
                
                # Check if new tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student'")
                new_tables_exist = cursor.fetchone() is not None
                
                return {
                    'legacy_records': legacy_count,
                    'new_schema_exists': new_tables_exist,
                    'legacy_table_exists': legacy_table_exists
                }
        
        except Exception as e:
            logger.error(f"Failed to check legacy data: {e}")
            return {'error': str(e)}
    
    def migrate_legacy_data(self):
        """Migrate data from legacy Add model to new models"""
        try:
            from attendance import app, db
            from attendance.models import Add, Student, Class, ClassEnrollment
            
            with app.app_context():
                # Get all legacy records
                legacy_records = Add.query.all()
                
                if not legacy_records:
                    logger.info("No legacy data to migrate")
                    return
                
                # Group by class
                classes_data = {}
                for record in legacy_records:
                    if record.classname and record.classname not in classes_data:
                        classes_data[record.classname] = {
                            'coordinator': record.coordinator,
                            'co_email': record.co_email,
                            'students': []
                        }
                    
                    if record.stuname and record.regno:
                        classes_data[record.classname]['students'].append({
                            'name': record.stuname,
                            'regno': str(record.regno),
                            'mobile': str(record.mobileno) if record.mobileno else None
                        })
                
                # Create new records
                for class_name, class_data in classes_data.items():
                    # Create class
                    new_class = Class(
                        name=class_name,
                        coordinator=class_data['coordinator'] or 'Unknown',
                        coordinator_email=class_data['co_email'] or 'unknown@example.com'
                    )
                    db.session.add(new_class)
                    db.session.flush()  # Get the ID
                    
                    # Create students and enrollments
                    for student_data in class_data['students']:
                        # Check if student already exists
                        existing_student = Student.query.filter_by(
                            registration_number=student_data['regno']
                        ).first()
                        
                        if not existing_student:
                            new_student = Student(
                                name=student_data['name'],
                                registration_number=student_data['regno'],
                                phone=student_data['mobile']
                            )
                            db.session.add(new_student)
                            db.session.flush()
                            student_id = new_student.id
                        else:
                            student_id = existing_student.id
                        
                        # Create enrollment
                        enrollment = ClassEnrollment(
                            student_id=student_id,
                            class_id=new_class.id
                        )
                        db.session.add(enrollment)
                
                db.session.commit()
                logger.info(f"Migrated {len(classes_data)} classes with students")
            
        except Exception as e:
            logger.error(f"Failed to migrate legacy data: {e}")
            raise
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            status = {}
            
            # Check if database exists
            if self.db_path:
                status['database_exists'] = Path(self.db_path).exists()
            else:
                status['database_exists'] = self.health_check()
            
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
    
    def migrate_to_new_schema(self) -> bool:
        """Migrate from legacy schema to new schema"""
        try:
            logger.info("Starting migration to new schema...")
            
            # Check legacy data
            legacy_info = self.check_legacy_data()
            
            if not legacy_info.get('legacy_records', 0):
                logger.info("No legacy data to migrate")
            else:
                logger.info(f"Found {legacy_info['legacy_records']} legacy records to migrate")
            
            # Create new tables
            logger.info("Creating new database schema...")
            self.create_tables()
            
            # Migrate legacy data if it exists
            if legacy_info.get('legacy_records', 0) > 0:
                logger.info("Migrating legacy data...")
                self.migrate_legacy_data()
            
            logger.info("Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def verify_migration(self) -> Dict[str, Any]:
        """Verify that migration was successful"""
        try:
            verification_results = {}
            
            # Check database health
            verification_results['database_healthy'] = self.health_check()
            
            # Check table existence and counts
            try:
                from attendance import app
                from attendance.models import Student, Class
                
                with app.app_context():
                    student_count = Student.query.count()
                    class_count = Class.query.count()
                    
                    verification_results['students_count'] = student_count
                    verification_results['classes_count'] = class_count
                    verification_results['tables_accessible'] = True
                
            except Exception as e:
                verification_results['tables_accessible'] = False
                verification_results['table_error'] = str(e)
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return {'error': str(e)}


# Global instance
simple_db_manager = SimpleDatabaseManager()