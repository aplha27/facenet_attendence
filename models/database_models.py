"""
SQLAlchemy database models for the attendance system
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
import enum

# Import the existing db instance
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from attendance import db, login_manager

# Enums
class AttendanceStatusEnum(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    registration_number = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_enrollments = relationship("ClassEnrollment", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="student", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Student('{self.name}', '{self.registration_number}')"


class Class(db.Model):
    """Class model"""
    __tablename__ = 'classes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    coordinator = Column(String(100), nullable=False)
    coordinator_email = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = relationship("ClassEnrollment", back_populates="class_", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="class_", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="class_", cascade="all, delete-orphan")
    
    @property
    def students(self):
        """Get all students enrolled in this class"""
        return [enrollment.student for enrollment in self.enrollments]
    
    def __repr__(self):
        return f"Class('{self.name}', '{self.coordinator}')"


class ClassEnrollment(db.Model):
    """Many-to-many relationship between students and classes"""
    __tablename__ = 'class_enrollments'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="class_enrollments")
    class_ = relationship("Class", back_populates="enrollments")
    
    def __repr__(self):
        return f"ClassEnrollment(student_id={self.student_id}, class_id={self.class_id})"


class AttendanceRecord(db.Model):
    """Attendance record model"""
    __tablename__ = 'attendance_records'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=True)
    date = Column(Date, nullable=False, default=date.today)
    status = Column(SQLEnum(AttendanceStatusEnum), nullable=False, default=AttendanceStatusEnum.ABSENT)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student", back_populates="attendance_records")
    class_ = relationship("Class", back_populates="attendance_records")
    session = relationship("AttendanceSession", back_populates="records")
    
    def __repr__(self):
        return f"AttendanceRecord(student_id={self.student_id}, class_id={self.class_id}, status={self.status.value})"


class AttendanceSession(db.Model):
    """Attendance session model"""
    __tablename__ = 'attendance_sessions'
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    image_path = Column(String(255), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    total_detected = Column(Integer, default=0)
    total_recognized = Column(Integer, default=0)
    
    # Relationships
    class_ = relationship("Class", back_populates="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"AttendanceSession(class_id={self.class_id}, date={self.date})"


# Legacy model for backward compatibility
class Add(db.Model):
    """Legacy model for backward compatibility"""
    __tablename__ = 'add'
    
    id = Column(Integer, primary_key=True)
    classname = Column(String(20), unique=True)
    coordinator = Column(String(30), unique=True)
    co_email = Column(String(30), unique=True)
    stuname = Column(String(30), unique=True)
    regno = Column(Integer, unique=True)
    mobileno = Column(Integer, unique=True)
    
    def __repr__(self):
        return f"Add('{self.classname}', '{self.coordinator}', '{self.co_email}', '{self.stuname}', '{self.regno}', '{self.mobileno}')"