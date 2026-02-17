"""
Core domain models for the attendance system
"""

from datetime import datetime, date
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import numpy as np


class AttendanceStatus(Enum):
    """Attendance status enumeration"""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


@dataclass
class Student:
    """Student domain model"""
    id: Optional[int]
    name: str
    registration_number: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class Class:
    """Class domain model"""
    id: Optional[int]
    name: str
    coordinator: str
    coordinator_email: str
    students: Optional[List[Student]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.students is None:
            self.students = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class AttendanceRecord:
    """Attendance record domain model"""
    id: Optional[int]
    student_id: int
    class_id: int
    date: date
    status: AttendanceStatus
    confidence_score: Optional[float] = None
    image_path: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class BoundingBox:
    """Bounding box for face detection"""
    x: int
    y: int
    width: int
    height: int


@dataclass
class Point:
    """2D point for landmarks"""
    x: float
    y: float


@dataclass
class FaceDetection:
    """Face detection result"""
    bounding_box: BoundingBox
    confidence: float
    landmarks: Optional[List[Point]] = None


@dataclass
class Recognition:
    """Face recognition result"""
    student_id: Optional[int]
    confidence: float
    embedding: Optional[np.ndarray] = None
    
    def __post_init__(self):
        # Convert numpy array to list for serialization if needed
        if self.embedding is not None and isinstance(self.embedding, np.ndarray):
            self.embedding = self.embedding.tolist()


@dataclass
class AttendanceSession:
    """Attendance session for a class"""
    id: Optional[int]
    class_id: int
    date: date
    image_path: Optional[str] = None
    processed_at: Optional[datetime] = None
    total_detected: int = 0
    total_recognized: int = 0
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.utcnow()


@dataclass
class AttendanceStats:
    """Attendance statistics"""
    class_id: int
    total_students: int
    total_sessions: int
    average_attendance: float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int