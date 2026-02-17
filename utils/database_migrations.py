"""
Database migration utilities for the Attendance System

Handles database schema migrations and data migrations from legacy structure
to the new modernized structure.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.database_manager import db_manager, DatabaseError
from services.repositories import legacy_repo, user_repo, class_repo, student_repo, enrollment_repo
from models.domain_models import Base

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Handles database migrations and schema updates"""
    
    def __init__(self):
        self.migration_history = []
    
    def initialize_database(self) -> Dict[str, Any]:
        """Initialize database with all tables"""
        try:
            logger.info("Initializing database...")
            
            # Create all tables
            db_manager.create_tables()
            
            # Perform health check
            health_status = db_manager.health_check()
            
            # Get table information
            table_info = db_manager.get_table_info()
            
            result = {
                "status": "success",
                "message": "Database initialized successfully",
                "health_check": health_status,
                "table_info": table_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Database initialization completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return {
                "status": "error",
                "message": f"Database initialization failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def migrate_legacy_data(self) -> Dict[str, Any]:
        """Migrate data from legacy Add table to new structure"""
        try:
            logger.info("Starting legacy data migration...")
            
            # Check if legacy data exists
            legacy_data = legacy_repo.get_all_legacy_data()
            if not legacy_data:
                return {
                    "status": "success",
                    "message": "No legacy data found to migrate",
                    "migrated_counts": {"classes": 0, "students": 0, "enrollments": 0}
                }
            
            logger.info(f"Found {len(legacy_data)} legacy records to migrate")
            
            # Perform migration
            migrated_counts = legacy_repo.migrate_to_new_structure()
            
            result = {
                "status": "success",
                "message": "Legacy data migration completed successfully",
                "legacy_records_found": len(legacy_data),
                "migrated_counts": migrated_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Legacy data migration completed: {migrated_counts}")
            return result
            
        except Exception as e:
            logger.error(f"Legacy data migration failed: {e}")
            return {
                "status": "error",
                "message": f"Legacy data migration failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_sample_data(self) -> Dict[str, Any]:
        """Create sample data for testing and demonstration"""
        try:
            logger.info("Creating sample data...")
            
            created_counts = {
                "users": 0,
                "classes": 0,
                "students": 0,
                "enrollments": 0
            }
            
            # Create sample users
            sample_users = [
                {"username": "admin", "email": "admin@example.com", "password": "admin123"},
                {"username": "teacher1", "email": "teacher1@example.com", "password": "teacher123"},
                {"username": "coordinator", "email": "coordinator@example.com", "password": "coord123"}
            ]
            
            for user_data in sample_users:
                try:
                    existing_user = user_repo.get_by_email(user_data["email"])
                    if not existing_user:
                        user_repo.create_user(**user_data)
                        created_counts["users"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create user {user_data['username']}: {e}")
            
            # Create sample classes
            sample_classes = [
                {
                    "name": "Computer Science 101",
                    "coordinator": "Dr. Smith",
                    "coordinator_email": "dr.smith@example.com",
                    "description": "Introduction to Computer Science"
                },
                {
                    "name": "Mathematics 201",
                    "coordinator": "Prof. Johnson",
                    "coordinator_email": "prof.johnson@example.com",
                    "description": "Advanced Mathematics"
                },
                {
                    "name": "Physics 301",
                    "coordinator": "Dr. Brown",
                    "coordinator_email": "dr.brown@example.com",
                    "description": "Advanced Physics"
                }
            ]
            
            created_classes = []
            for class_data in sample_classes:
                try:
                    existing_class = class_repo.get_by_name(class_data["name"])
                    if not existing_class:
                        new_class = class_repo.create_class(**class_data)
                        created_classes.append(new_class)
                        created_counts["classes"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create class {class_data['name']}: {e}")
            
            # Create sample students
            sample_students = [
                {"name": "John Doe", "registration_number": "CS2024001", "email": "john.doe@student.com"},
                {"name": "Jane Smith", "registration_number": "CS2024002", "email": "jane.smith@student.com"},
                {"name": "Bob Johnson", "registration_number": "CS2024003", "email": "bob.johnson@student.com"},
                {"name": "Alice Brown", "registration_number": "MATH2024001", "email": "alice.brown@student.com"},
                {"name": "Charlie Wilson", "registration_number": "MATH2024002", "email": "charlie.wilson@student.com"},
                {"name": "Diana Davis", "registration_number": "PHYS2024001", "email": "diana.davis@student.com"}
            ]
            
            created_students = []
            for student_data in sample_students:
                try:
                    existing_student = student_repo.get_by_registration_number(
                        student_data["registration_number"]
                    )
                    if not existing_student:
                        new_student = student_repo.create_student(**student_data)
                        created_students.append(new_student)
                        created_counts["students"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create student {student_data['name']}: {e}")
            
            # Enroll students in classes
            if created_classes and created_students:
                # Get fresh instances from database to avoid session issues
                all_classes = class_repo.get_all()
                all_students = student_repo.get_all()
                
                # Enroll CS students in CS class
                cs_class = next((c for c in all_classes if "Computer Science" in c.name), None)
                if cs_class:
                    cs_students = [s for s in all_students if s.registration_number.startswith("CS")]
                    for student in cs_students:
                        try:
                            enrollment_repo.enroll_student(student.id, cs_class.id)
                            created_counts["enrollments"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to enroll student {student.name}: {e}")
                
                # Enroll Math students in Math class
                math_class = next((c for c in all_classes if "Mathematics" in c.name), None)
                if math_class:
                    math_students = [s for s in all_students if s.registration_number.startswith("MATH")]
                    for student in math_students:
                        try:
                            enrollment_repo.enroll_student(student.id, math_class.id)
                            created_counts["enrollments"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to enroll student {student.name}: {e}")
                
                # Enroll Physics students in Physics class
                phys_class = next((c for c in all_classes if "Physics" in c.name), None)
                if phys_class:
                    phys_students = [s for s in all_students if s.registration_number.startswith("PHYS")]
                    for student in phys_students:
                        try:
                            enrollment_repo.enroll_student(student.id, phys_class.id)
                            created_counts["enrollments"] += 1
                        except Exception as e:
                            logger.warning(f"Failed to enroll student {student.name}: {e}")
            
            result = {
                "status": "success",
                "message": "Sample data created successfully",
                "created_counts": created_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Sample data creation completed: {created_counts}")
            return result
            
        except Exception as e:
            logger.error(f"Sample data creation failed: {e}")
            return {
                "status": "error",
                "message": f"Sample data creation failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def backup_database(self, backup_name: str = None) -> Dict[str, Any]:
        """Create a database backup"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = Path("backups") / backup_name
            success = db_manager.backup_database(backup_path)
            
            if success:
                return {
                    "status": "success",
                    "message": "Database backup created successfully",
                    "backup_path": str(backup_path),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Database backup failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                "status": "error",
                "message": f"Database backup failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration and database status"""
        try:
            # Get database health
            health_status = db_manager.health_check()
            
            # Get table information
            table_info = db_manager.get_table_info()
            
            # Check for legacy data
            legacy_count = legacy_repo.count()
            
            # Get current data counts
            current_counts = {
                "users": user_repo.count(),
                "classes": class_repo.count(),
                "students": student_repo.count(),
                "enrollments": enrollment_repo.count()
            }
            
            return {
                "status": "success",
                "database_health": health_status,
                "table_info": table_info,
                "legacy_records": legacy_count,
                "current_counts": current_counts,
                "migration_needed": legacy_count > 0 and current_counts["classes"] == 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "status": "error",
                "message": f"Failed to get migration status: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def reset_database(self, confirm: bool = False) -> Dict[str, Any]:
        """Reset database (drop and recreate all tables) - USE WITH CAUTION"""
        if not confirm:
            return {
                "status": "error",
                "message": "Database reset requires explicit confirmation",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            logger.warning("Resetting database - all data will be lost!")
            
            # Drop all tables
            db_manager.drop_tables()
            
            # Recreate tables
            db_manager.create_tables()
            
            return {
                "status": "success",
                "message": "Database reset completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return {
                "status": "error",
                "message": f"Database reset failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }


# Global migration instance
migration_manager = DatabaseMigration()