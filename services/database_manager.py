"""
Database Manager for handling database operations with error recovery
"""

import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import time

# Import configuration and models
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.configuration_manager import config_manager
from models.database_models import db, User, Student, Class, ClassEnrollment, AttendanceRecord, AttendanceSession, Add
from models.domain_models import Student as DomainStudent, Class as DomainClass, AttendanceRecord as DomainAttendanceRecord

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom database error"""
    pass


class DatabaseManager:
    """Manages database operations with error handling and recovery"""
    
    def __init__(self):
        self.db = db
        self._connection_retries = 3
        self._retry_delay = 1.0
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.db.session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            # Session is managed by Flask-SQLAlchemy, no need to close
            pass
    
    def _retry_operation(self, operation, *args, **kwargs):
        """Retry database operation with exponential backoff"""
        last_exception = None
        
        for attempt in range(self._connection_retries):
            try:
                return operation(*args, **kwargs)
            except (OperationalError, DatabaseError) as e:
                last_exception = e
                if attempt < self._connection_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(f"Database operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Database operation failed after {self._connection_retries} attempts: {e}")
        
        raise DatabaseError(f"Database operation failed after {self._connection_retries} attempts: {last_exception}")
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            self.db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseError(f"Failed to create tables: {e}")
    
    def migrate_legacy_data(self):
        """Migrate data from legacy Add model to new models"""
        try:
            with self.get_session() as session:
                # Get all legacy records
                legacy_records = session.query(Add).all()
                
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
                            'regno': record.regno,
                            'mobile': record.mobileno
                        })
                
                # Create new records
                for class_name, class_data in classes_data.items():
                    # Create class
                    new_class = Class(
                        name=class_name,
                        coordinator=class_data['coordinator'] or 'Unknown',
                        coordinator_email=class_data['co_email'] or 'unknown@example.com'
                    )
                    session.add(new_class)
                    session.flush()  # Get the ID
                    
                    # Create students and enrollments
                    for student_data in class_data['students']:
                        # Check if student already exists
                        existing_student = session.query(Student).filter_by(
                            registration_number=str(student_data['regno'])
                        ).first()
                        
                        if not existing_student:
                            new_student = Student(
                                name=student_data['name'],
                                registration_number=str(student_data['regno']),
                                phone=str(student_data['mobile']) if student_data['mobile'] else None
                            )
                            session.add(new_student)
                            session.flush()
                            student_id = new_student.id
                        else:
                            student_id = existing_student.id
                        
                        # Create enrollment
                        enrollment = ClassEnrollment(
                            student_id=student_id,
                            class_id=new_class.id
                        )
                        session.add(enrollment)
                
                logger.info(f"Migrated {len(classes_data)} classes with students")
                
        except Exception as e:
            logger.error(f"Failed to migrate legacy data: {e}")
            raise DatabaseError(f"Migration failed: {e}")


class StudentRepository:
    """Repository for student operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create(self, student: DomainStudent) -> DomainStudent:
        """Create a new student"""
        def _create():
            with self.db_manager.get_session() as session:
                db_student = Student(
                    name=student.name,
                    registration_number=student.registration_number,
                    email=student.email,
                    phone=student.phone
                )
                session.add(db_student)
                session.flush()
                
                # Convert back to domain model
                return DomainStudent(
                    id=db_student.id,
                    name=db_student.name,
                    registration_number=db_student.registration_number,
                    email=db_student.email,
                    phone=db_student.phone,
                    created_at=db_student.created_at,
                    updated_at=db_student.updated_at
                )
        
        return self.db_manager._retry_operation(_create)
    
    def get_by_id(self, student_id: int) -> Optional[DomainStudent]:
        """Get student by ID"""
        def _get():
            with self.db_manager.get_session() as session:
                db_student = session.query(Student).filter_by(id=student_id).first()
                if not db_student:
                    return None
                
                return DomainStudent(
                    id=db_student.id,
                    name=db_student.name,
                    registration_number=db_student.registration_number,
                    email=db_student.email,
                    phone=db_student.phone,
                    created_at=db_student.created_at,
                    updated_at=db_student.updated_at
                )
        
        return self.db_manager._retry_operation(_get)
    
    def get_by_registration_number(self, reg_number: str) -> Optional[DomainStudent]:
        """Get student by registration number"""
        def _get():
            with self.db_manager.get_session() as session:
                db_student = session.query(Student).filter_by(registration_number=reg_number).first()
                if not db_student:
                    return None
                
                return DomainStudent(
                    id=db_student.id,
                    name=db_student.name,
                    registration_number=db_student.registration_number,
                    email=db_student.email,
                    phone=db_student.phone,
                    created_at=db_student.created_at,
                    updated_at=db_student.updated_at
                )
        
        return self.db_manager._retry_operation(_get)
    
    def get_all(self) -> List[DomainStudent]:
        """Get all students"""
        def _get_all():
            with self.db_manager.get_session() as session:
                db_students = session.query(Student).all()
                
                return [
                    DomainStudent(
                        id=s.id,
                        name=s.name,
                        registration_number=s.registration_number,
                        email=s.email,
                        phone=s.phone,
                        created_at=s.created_at,
                        updated_at=s.updated_at
                    )
                    for s in db_students
                ]
        
        return self.db_manager._retry_operation(_get_all)
    
    def update(self, student: DomainStudent) -> DomainStudent:
        """Update student"""
        def _update():
            with self.db_manager.get_session() as session:
                db_student = session.query(Student).filter_by(id=student.id).first()
                if not db_student:
                    raise DatabaseError(f"Student with ID {student.id} not found")
                
                db_student.name = student.name
                db_student.registration_number = student.registration_number
                db_student.email = student.email
                db_student.phone = student.phone
                
                session.flush()
                
                return DomainStudent(
                    id=db_student.id,
                    name=db_student.name,
                    registration_number=db_student.registration_number,
                    email=db_student.email,
                    phone=db_student.phone,
                    created_at=db_student.created_at,
                    updated_at=db_student.updated_at
                )
        
        return self.db_manager._retry_operation(_update)
    
    def delete(self, student_id: int) -> bool:
        """Delete student"""
        def _delete():
            with self.db_manager.get_session() as session:
                db_student = session.query(Student).filter_by(id=student_id).first()
                if not db_student:
                    return False
                
                session.delete(db_student)
                return True
        
        return self.db_manager._retry_operation(_delete)


class ClassRepository:
    """Repository for class operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create(self, class_obj: DomainClass) -> DomainClass:
        """Create a new class"""
        def _create():
            with self.db_manager.get_session() as session:
                db_class = Class(
                    name=class_obj.name,
                    coordinator=class_obj.coordinator,
                    coordinator_email=class_obj.coordinator_email
                )
                session.add(db_class)
                session.flush()
                
                return DomainClass(
                    id=db_class.id,
                    name=db_class.name,
                    coordinator=db_class.coordinator,
                    coordinator_email=db_class.coordinator_email,
                    students=[],
                    created_at=db_class.created_at,
                    updated_at=db_class.updated_at
                )
        
        return self.db_manager._retry_operation(_create)
    
    def get_by_id(self, class_id: int) -> Optional[DomainClass]:
        """Get class by ID with enrolled students"""
        def _get():
            with self.db_manager.get_session() as session:
                db_class = session.query(Class).filter_by(id=class_id).first()
                if not db_class:
                    return None
                
                # Get enrolled students
                students = [
                    DomainStudent(
                        id=s.id,
                        name=s.name,
                        registration_number=s.registration_number,
                        email=s.email,
                        phone=s.phone,
                        created_at=s.created_at,
                        updated_at=s.updated_at
                    )
                    for s in db_class.students
                ]
                
                return DomainClass(
                    id=db_class.id,
                    name=db_class.name,
                    coordinator=db_class.coordinator,
                    coordinator_email=db_class.coordinator_email,
                    students=students,
                    created_at=db_class.created_at,
                    updated_at=db_class.updated_at
                )
        
        return self.db_manager._retry_operation(_get)
    
    def get_all(self) -> List[DomainClass]:
        """Get all classes"""
        def _get_all():
            with self.db_manager.get_session() as session:
                db_classes = session.query(Class).all()
                
                result = []
                for db_class in db_classes:
                    students = [
                        DomainStudent(
                            id=s.id,
                            name=s.name,
                            registration_number=s.registration_number,
                            email=s.email,
                            phone=s.phone,
                            created_at=s.created_at,
                            updated_at=s.updated_at
                        )
                        for s in db_class.students
                    ]
                    
                    result.append(DomainClass(
                        id=db_class.id,
                        name=db_class.name,
                        coordinator=db_class.coordinator,
                        coordinator_email=db_class.coordinator_email,
                        students=students,
                        created_at=db_class.created_at,
                        updated_at=db_class.updated_at
                    ))
                
                return result
        
        return self.db_manager._retry_operation(_get_all)
    
    def add_student(self, class_id: int, student_id: int) -> bool:
        """Add student to class"""
        def _add_student():
            with self.db_manager.get_session() as session:
                # Check if enrollment already exists
                existing = session.query(ClassEnrollment).filter_by(
                    class_id=class_id,
                    student_id=student_id
                ).first()
                
                if existing:
                    return False
                
                enrollment = ClassEnrollment(
                    class_id=class_id,
                    student_id=student_id
                )
                session.add(enrollment)
                return True
        
        return self.db_manager._retry_operation(_add_student)
    
    def remove_student(self, class_id: int, student_id: int) -> bool:
        """Remove student from class"""
        def _remove_student():
            with self.db_manager.get_session() as session:
                enrollment = session.query(ClassEnrollment).filter_by(
                    class_id=class_id,
                    student_id=student_id
                ).first()
                
                if not enrollment:
                    return False
                
                session.delete(enrollment)
                return True
        
        return self.db_manager._retry_operation(_remove_student)


# Global instances
database_manager = DatabaseManager()
student_repository = StudentRepository(database_manager)
class_repository = ClassRepository(database_manager)