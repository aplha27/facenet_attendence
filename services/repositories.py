"""
Repository pattern implementations for data access abstraction

Provides clean interfaces for database operations with proper error handling
and business logic separation.
"""

import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, desc, asc
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.domain_models import (
    User, Student, Class, ClassEnrollment, AttendanceSession, 
    AttendanceRecord, AttendanceStatus, Add
)
from services.database_manager import db_manager, DatabaseError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        def _create(session: Session):
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.flush()  # Get the ID without committing
            return instance
        
        return db_manager.execute_with_retry(_create)
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """Get record by ID"""
        def _get(session: Session):
            return session.query(self.model_class).filter_by(id=record_id).first()
        
        return db_manager.execute_with_retry(_get)
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all records with optional pagination"""
        def _get_all(session: Session):
            query = session.query(self.model_class)
            if limit:
                query = query.limit(limit).offset(offset)
            return query.all()
        
        return db_manager.execute_with_retry(_get_all)
    
    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """Update record by ID"""
        def _update(session: Session):
            instance = session.query(self.model_class).filter_by(id=record_id).first()
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.flush()
            return instance
        
        return db_manager.execute_with_retry(_update)
    
    def delete(self, record_id: int) -> bool:
        """Delete record by ID"""
        def _delete(session: Session):
            instance = session.query(self.model_class).filter_by(id=record_id).first()
            if instance:
                session.delete(instance)
                return True
            return False
        
        return db_manager.execute_with_retry(_delete)
    
    def count(self) -> int:
        """Count total records"""
        def _count(session: Session):
            return session.query(self.model_class).count()
        
        return db_manager.execute_with_retry(_count)


class UserRepository(BaseRepository):
    """Repository for User operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        def _get(session: Session):
            return session.query(User).filter_by(username=username).first()
        
        return db_manager.execute_with_retry(_get)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        def _get(session: Session):
            return session.query(User).filter_by(email=email.lower()).first()
        
        return db_manager.execute_with_retry(_get)
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user with validation"""
        try:
            return self.create(
                username=username,
                email=email.lower(),
                password=password
            )
        except IntegrityError as e:
            if "username" in str(e):
                raise DatabaseError("Username already exists")
            elif "email" in str(e):
                raise DatabaseError("Email already exists")
            else:
                raise DatabaseError("User creation failed")
    
    def get_active_users(self) -> List[User]:
        """Get all active users"""
        def _get_active(session: Session):
            return session.query(User).filter_by(is_active=True).all()
        
        return db_manager.execute_with_retry(_get_active)


class StudentRepository(BaseRepository):
    """Repository for Student operations"""
    
    def __init__(self):
        super().__init__(Student)
    
    def get_by_registration_number(self, reg_num: str) -> Optional[Student]:
        """Get student by registration number"""
        def _get(session: Session):
            return session.query(Student).filter_by(
                registration_number=reg_num.upper()
            ).first()
        
        return db_manager.execute_with_retry(_get)
    
    def search_by_name(self, name_pattern: str) -> List[Student]:
        """Search students by name pattern"""
        def _search(session: Session):
            return session.query(Student).filter(
                Student.name.ilike(f"%{name_pattern}%")
            ).all()
        
        return db_manager.execute_with_retry(_search)
    
    def get_active_students(self) -> List[Student]:
        """Get all active students"""
        def _get_active(session: Session):
            return session.query(Student).filter_by(is_active=True).all()
        
        return db_manager.execute_with_retry(_get_active)
    
    def create_student(self, name: str, registration_number: str, 
                      email: Optional[str] = None, phone: Optional[str] = None) -> Student:
        """Create a new student with validation"""
        try:
            return self.create(
                name=name,
                registration_number=registration_number.upper(),
                email=email.lower() if email else None,
                phone=phone
            )
        except IntegrityError as e:
            if "registration_number" in str(e):
                raise DatabaseError("Registration number already exists")
            elif "email" in str(e):
                raise DatabaseError("Email already exists")
            else:
                raise DatabaseError("Student creation failed")


class ClassRepository(BaseRepository):
    """Repository for Class operations"""
    
    def __init__(self):
        super().__init__(Class)
    
    def get_by_name(self, name: str) -> Optional[Class]:
        """Get class by name"""
        def _get(session: Session):
            return session.query(Class).filter_by(name=name).first()
        
        return db_manager.execute_with_retry(_get)
    
    def get_active_classes(self) -> List[Class]:
        """Get all active classes"""
        def _get_active(session: Session):
            return session.query(Class).filter_by(is_active=True).all()
        
        return db_manager.execute_with_retry(_get_active)
    
    def get_classes_by_coordinator(self, coordinator_email: str) -> List[Class]:
        """Get classes by coordinator email"""
        def _get_by_coordinator(session: Session):
            return session.query(Class).filter_by(
                coordinator_email=coordinator_email.lower()
            ).all()
        
        return db_manager.execute_with_retry(_get_by_coordinator)
    
    def create_class(self, name: str, coordinator: str, coordinator_email: str,
                    description: Optional[str] = None, coordinator_user_id: Optional[int] = None) -> Class:
        """Create a new class"""
        return self.create(
            name=name,
            coordinator=coordinator,
            coordinator_email=coordinator_email.lower(),
            description=description,
            coordinator_user_id=coordinator_user_id
        )


class ClassEnrollmentRepository(BaseRepository):
    """Repository for ClassEnrollment operations"""
    
    def __init__(self):
        super().__init__(ClassEnrollment)
    
    def enroll_student(self, student_id: int, class_id: int) -> ClassEnrollment:
        """Enroll a student in a class"""
        try:
            return self.create(
                student_id=student_id,
                class_id=class_id
            )
        except IntegrityError:
            raise DatabaseError("Student is already enrolled in this class")
    
    def get_class_students(self, class_id: int, active_only: bool = True) -> List[Student]:
        """Get all students enrolled in a class"""
        def _get_students(session: Session):
            query = session.query(Student).join(ClassEnrollment).filter(
                ClassEnrollment.class_id == class_id
            )
            if active_only:
                query = query.filter(ClassEnrollment.is_active == True)
            return query.all()
        
        return db_manager.execute_with_retry(_get_students)
    
    def get_student_classes(self, student_id: int, active_only: bool = True) -> List[Class]:
        """Get all classes a student is enrolled in"""
        def _get_classes(session: Session):
            query = session.query(Class).join(ClassEnrollment).filter(
                ClassEnrollment.student_id == student_id
            )
            if active_only:
                query = query.filter(ClassEnrollment.is_active == True)
            return query.all()
        
        return db_manager.execute_with_retry(_get_classes)
    
    def unenroll_student(self, student_id: int, class_id: int) -> bool:
        """Unenroll a student from a class (soft delete)"""
        def _unenroll(session: Session):
            enrollment = session.query(ClassEnrollment).filter_by(
                student_id=student_id,
                class_id=class_id,
                is_active=True
            ).first()
            if enrollment:
                enrollment.is_active = False
                return True
            return False
        
        return db_manager.execute_with_retry(_unenroll)


class AttendanceSessionRepository(BaseRepository):
    """Repository for AttendanceSession operations"""
    
    def __init__(self):
        super().__init__(AttendanceSession)
    
    def create_session(self, class_id: int, session_date: date, 
                      image_path: Optional[str] = None,
                      processed_by_user_id: Optional[int] = None) -> AttendanceSession:
        """Create a new attendance session"""
        return self.create(
            class_id=class_id,
            session_date=session_date,
            image_path=image_path,
            processed_by_user_id=processed_by_user_id
        )
    
    def get_class_sessions(self, class_id: int, limit: Optional[int] = None) -> List[AttendanceSession]:
        """Get attendance sessions for a class"""
        def _get_sessions(session: Session):
            query = session.query(AttendanceSession).filter_by(
                class_id=class_id
            ).order_by(desc(AttendanceSession.session_date))
            if limit:
                query = query.limit(limit)
            return query.all()
        
        return db_manager.execute_with_retry(_get_sessions)
    
    def get_sessions_by_date_range(self, class_id: int, start_date: date, 
                                  end_date: date) -> List[AttendanceSession]:
        """Get sessions within a date range"""
        def _get_sessions(session: Session):
            return session.query(AttendanceSession).filter(
                and_(
                    AttendanceSession.class_id == class_id,
                    AttendanceSession.session_date >= start_date,
                    AttendanceSession.session_date <= end_date
                )
            ).order_by(AttendanceSession.session_date).all()
        
        return db_manager.execute_with_retry(_get_sessions)


class AttendanceRecordRepository(BaseRepository):
    """Repository for AttendanceRecord operations"""
    
    def __init__(self):
        super().__init__(AttendanceRecord)
    
    def mark_attendance(self, student_id: int, session_id: int, 
                       status: str, confidence_score: Optional[float] = None,
                       detection_method: str = "automatic",
                       marked_by_user_id: Optional[int] = None) -> AttendanceRecord:
        """Mark attendance for a student"""
        try:
            return self.create(
                student_id=student_id,
                session_id=session_id,
                status=status,
                confidence_score=confidence_score,
                detection_method=detection_method,
                marked_by_user_id=marked_by_user_id
            )
        except IntegrityError:
            raise DatabaseError("Attendance already marked for this student in this session")
    
    def get_session_attendance(self, session_id: int) -> List[AttendanceRecord]:
        """Get all attendance records for a session"""
        def _get_attendance(session: Session):
            return session.query(AttendanceRecord).filter_by(
                session_id=session_id
            ).all()
        
        return db_manager.execute_with_retry(_get_attendance)
    
    def get_student_attendance(self, student_id: int, class_id: Optional[int] = None,
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> List[AttendanceRecord]:
        """Get attendance records for a student"""
        def _get_attendance(session: Session):
            query = session.query(AttendanceRecord).join(AttendanceSession).filter(
                AttendanceRecord.student_id == student_id
            )
            
            if class_id:
                query = query.filter(AttendanceSession.class_id == class_id)
            
            if start_date:
                query = query.filter(AttendanceSession.session_date >= start_date)
            
            if end_date:
                query = query.filter(AttendanceSession.session_date <= end_date)
            
            return query.order_by(AttendanceSession.session_date).all()
        
        return db_manager.execute_with_retry(_get_attendance)
    
    def update_attendance(self, student_id: int, session_id: int, 
                         status: str, notes: Optional[str] = None) -> Optional[AttendanceRecord]:
        """Update existing attendance record"""
        def _update_attendance(session: Session):
            record = session.query(AttendanceRecord).filter_by(
                student_id=student_id,
                session_id=session_id
            ).first()
            
            if record:
                record.status = status
                if notes:
                    record.notes = notes
                record.marked_at = datetime.utcnow()
                session.flush()
            
            return record
        
        return db_manager.execute_with_retry(_update_attendance)


class LegacyRepository(BaseRepository):
    """Repository for legacy Add model (for migration purposes)"""
    
    def __init__(self):
        super().__init__(Add)
    
    def get_all_legacy_data(self) -> List[Add]:
        """Get all legacy data for migration"""
        return self.get_all()
    
    def migrate_to_new_structure(self) -> Dict[str, int]:
        """Migrate legacy data to new structure"""
        def _migrate(session: Session):
            legacy_records = session.query(Add).all()
            
            migrated_counts = {
                'classes': 0,
                'students': 0,
                'enrollments': 0
            }
            
            class_repo = ClassRepository()
            student_repo = StudentRepository()
            enrollment_repo = ClassEnrollmentRepository()
            
            # Group records by class
            classes_data = {}
            for record in legacy_records:
                if record.classname not in classes_data:
                    classes_data[record.classname] = {
                        'coordinator': record.coordinator,
                        'coordinator_email': record.co_email,
                        'students': []
                    }
                
                if record.stuname:  # Only add if student name exists
                    classes_data[record.classname]['students'].append({
                        'name': record.stuname,
                        'registration_number': str(record.regno) if record.regno else '',
                        'phone': str(record.mobileno) if record.mobileno else None
                    })
            
            # Create new structure
            for class_name, class_data in classes_data.items():
                try:
                    # Create class
                    new_class = class_repo.create_class(
                        name=class_name,
                        coordinator=class_data['coordinator'],
                        coordinator_email=class_data['coordinator_email']
                    )
                    migrated_counts['classes'] += 1
                    
                    # Create students and enroll them
                    for student_data in class_data['students']:
                        if student_data['name'] and student_data['registration_number']:
                            try:
                                # Check if student already exists
                                existing_student = student_repo.get_by_registration_number(
                                    student_data['registration_number']
                                )
                                
                                if not existing_student:
                                    new_student = student_repo.create_student(
                                        name=student_data['name'],
                                        registration_number=student_data['registration_number'],
                                        phone=student_data['phone']
                                    )
                                    migrated_counts['students'] += 1
                                else:
                                    new_student = existing_student
                                
                                # Enroll student in class
                                enrollment_repo.enroll_student(new_student.id, new_class.id)
                                migrated_counts['enrollments'] += 1
                                
                            except Exception as e:
                                logger.warning(f"Failed to migrate student {student_data['name']}: {e}")
                
                except Exception as e:
                    logger.warning(f"Failed to migrate class {class_name}: {e}")
            
            return migrated_counts
        
        return db_manager.execute_with_retry(_migrate)


# Repository instances
user_repo = UserRepository()
student_repo = StudentRepository()
class_repo = ClassRepository()
enrollment_repo = ClassEnrollmentRepository()
session_repo = AttendanceSessionRepository()
attendance_repo = AttendanceRecordRepository()
legacy_repo = LegacyRepository()