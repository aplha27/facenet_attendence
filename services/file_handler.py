"""
Secure File Handler for the attendance system

Handles file uploads with comprehensive validation, security scanning,
and directory traversal protection.
"""

import os
import hashlib
import logging
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import tempfile
import shutil
import re
import time

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from PIL import Image
# import magic # Optional, currently unused in visible code

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.configuration_manager import config_manager

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Exception raised for security violations"""
    pass


@dataclass
class ValidationResult:
    """Result of file validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_info: Optional[Dict[str, Any]] = None


@dataclass
class FileInfo:
    """Information about a processed file"""
    original_name: str
    secure_name: str
    file_path: Path
    file_size: int
    mime_type: str
    file_hash: str
    upload_time: datetime


class SecurityScanner:
    """Security scanner for uploaded files"""
    
    def __init__(self):
        # Known malicious file signatures (simplified for demo)
        self.malicious_signatures = [
            b'\x4d\x5a',  # PE executable header
            b'\x7f\x45\x4c\x46',  # ELF executable header
            b'<script',  # Script tags
            b'javascript:',  # JavaScript URLs
            b'vbscript:',  # VBScript URLs
        ]
        
        # Suspicious patterns in filenames
        self.suspicious_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.com$', r'\.scr$',
            r'\.vbs$', r'\.js$', r'\.jar$', r'\.php$', r'\.asp$',
            r'\.jsp$', r'\.py$', r'\.pl$', r'\.sh$', r'\.ps1$'
        ]
    
    def scan_file_content(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Scan file content for malicious patterns"""
        warnings = []
        
        try:
            with open(file_path, 'rb') as f:
                # Read first 1KB for signature checking
                header = f.read(1024)
                
                # Check for malicious signatures
                for signature in self.malicious_signatures:
                    if signature in header:
                        warnings.append(f"Suspicious file signature detected")
                        break
                
                # For text-based files, check for suspicious content
                if file_path.suffix.lower() in ['.txt', '.html', '.htm', '.xml']:
                    try:
                        content = header.decode('utf-8', errors='ignore').lower()
                        if any(pattern in content for pattern in ['<script', 'javascript:', 'vbscript:']):
                            warnings.append("Suspicious script content detected")
                    except:
                        pass
            
            return len(warnings) == 0, warnings
            
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            return False, [f"Scan failed: {str(e)}"]


class FileHandler:
    """Handles secure file uploads"""

    def __init__(self):
        self.upload_directory = config_manager.get_upload_directory()
        self.allowed_extensions = config_manager.config.allowed_file_types
        self.max_file_size = config_manager.get_max_file_size()
        self.MAX_FILENAME_LENGTH = 255
        self.DANGEROUS_EXTENSIONS = {'php', 'phar', 'pl', 'py', 'asp', 'aspx', 'jsp', 'exe', 'sh', 'bat', 'cmd'}
        self.MALICIOUS_SIGNATURES = [
            b'\x4d\x5a',  # PE executable header (EXE, DLL)
            b'\x7f\x45\x4c\x46',  # ELF executable
        ]

    def validate_upload(self, file: FileStorage) -> ValidationResult:
        """
        Validate uploaded file
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        file_info = {}
        
        try:
            # Check if file exists
            if not file or not file.filename:
                errors.append("No file provided")
                return ValidationResult(False, errors, warnings)
            
            # Get file information
            original_filename = file.filename
            file_size = self._get_file_size(file)
            
            file_info = {
                'original_filename': original_filename,
                'file_size': file_size,
                'content_type': file.content_type
            }
            
            # Validate filename
            filename_validation = self._validate_filename(original_filename)
            if not filename_validation[0]:
                errors.extend(filename_validation[1])
            
            # Validate file size
            if file_size > self.max_file_size:
                errors.append(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")
            
            if file_size == 0:
                errors.append("File is empty")
            
            # Validate file extension
            extension_validation = self._validate_extension(original_filename)
            if not extension_validation[0]:
                errors.extend(extension_validation[1])
            
            # Validate MIME type
            mime_validation = self._validate_mime_type(file)
            if not mime_validation[0]:
                errors.extend(mime_validation[1])
            else:
                file_info['detected_mime_type'] = mime_validation[1]
            
            # Scan file content for malicious signatures
            content_validation = self._scan_file_content(file)
            if not content_validation[0]:
                errors.extend(content_validation[1])
            
            # Check for directory traversal attempts
            if self._has_directory_traversal(original_filename):
                errors.append("Filename contains directory traversal patterns")
            
            # Additional security checks
            security_warnings = self._perform_security_checks(file, original_filename)
            warnings.extend(security_warnings)
            
            is_valid = len(errors) == 0
            
            return ValidationResult(is_valid, errors, warnings, file_info)
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(False, errors, warnings, file_info)
    
    def _get_file_size(self, file: FileStorage) -> int:
        """Get file size safely"""
        try:
            # Save current position
            current_pos = file.tell()
            
            # Seek to end to get size
            file.seek(0, 2)
            size = file.tell()
            
            # Restore position
            file.seek(current_pos)
            
            return size
        except Exception:
            return 0
    
    def _validate_filename(self, filename: str) -> Tuple[bool, List[str]]:
        """Validate filename for security issues"""
        errors = []
        
        if not filename:
            errors.append("Filename is empty")
            return False, errors
        
        # Check filename length
        if len(filename) > self.MAX_FILENAME_LENGTH:
            errors.append(f"Filename too long (max {self.MAX_FILENAME_LENGTH} characters)")
        
        # Check for null bytes
        if '\x00' in filename:
            errors.append("Filename contains null bytes")
        
        # Check for control characters
        if any(ord(c) < 32 for c in filename if c not in '\t\n\r'):
            errors.append("Filename contains control characters")
        
        # Check for reserved names (Windows)
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            errors.append(f"Filename uses reserved name: {name_without_ext}")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.\.', r'[<>:"|?*]', r'^\s', r'\s$', r'\.{2,}', r'__'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, filename):
                errors.append(f"Filename contains suspicious pattern: {pattern}")
        
        return len(errors) == 0, errors
    
    def _validate_extension(self, filename: str) -> Tuple[bool, List[str]]:
        """Validate file extension"""
        errors = []
        
        # Get file extension
        extension = Path(filename).suffix.lower().lstrip('.')
        
        if not extension:
            errors.append("File has no extension")
            return False, errors
        
        # Check against dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            errors.append(f"File extension '{extension}' is not allowed for security reasons")
        
        # Check against allowed extensions
        if extension not in self.allowed_extensions:
            errors.append(f"File extension '{extension}' is not allowed. Allowed: {', '.join(self.allowed_extensions)}")
        
        return len(errors) == 0, errors
    
    def _validate_mime_type(self, file: FileStorage) -> Tuple[bool, List[str]]:
        """Validate MIME type by examining file content"""
        try:
            # Save current position
            current_pos = file.tell()
            
            # Read first few bytes for MIME detection
            file.seek(0)
            header = file.read(512)
            file.seek(current_pos)
            
            # Detect MIME type from content
            detected_mime = self._detect_mime_type(header)
            
            # Get expected MIME types for allowed extensions
            filename = file.filename or ''
            extension = Path(filename).suffix.lower().lstrip('.')
            expected_mimes = self._get_expected_mime_types(extension)
            
            if detected_mime and expected_mimes:
                if detected_mime not in expected_mimes:
                    return False, [f"File content ({detected_mime}) doesn't match extension ({extension})"]
            
            return True, detected_mime or 'unknown'
            
        except Exception as e:
            logger.warning(f"MIME type validation error: {e}")
            return True, 'unknown'  # Don't fail validation on MIME detection errors
    
    def _detect_mime_type(self, header: bytes) -> Optional[str]:
        """Detect MIME type from file header"""
        # Common image file signatures
        signatures = {
            b'\xff\xd8\xff': 'image/jpeg',
            b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a': 'image/png',
            b'\x47\x49\x46\x38': 'image/gif',
            b'\x42\x4d': 'image/bmp',
            b'\x52\x49\x46\x46': 'image/webp',  # Partial signature
        }
        
        for signature, mime_type in signatures.items():
            if header.startswith(signature):
                return mime_type
        
        return None
    
    def _get_expected_mime_types(self, extension: str) -> List[str]:
        """Get expected MIME types for file extension"""
        mime_map = {
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
            'gif': ['image/gif'],
            'bmp': ['image/bmp', 'image/x-ms-bmp'],
            'webp': ['image/webp'],
        }
        
        return mime_map.get(extension, [])
    
    def _scan_file_content(self, file: FileStorage) -> Tuple[bool, List[str]]:
        """Scan file content for malicious signatures"""
        try:
            # Save current position
            current_pos = file.tell()
            
            # Read first 1KB for signature scanning
            file.seek(0)
            content = file.read(1024)
            file.seek(current_pos)
            
            errors = []
            
            # Check for malicious signatures
            for signature in self.MALICIOUS_SIGNATURES:
                if signature in content:
                    errors.append("File contains potentially malicious content")
                    break
            
            # Check for embedded scripts in images
            if self._has_embedded_scripts(content):
                errors.append("File may contain embedded scripts")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.warning(f"Content scanning error: {e}")
            return True, []  # Don't fail validation on scanning errors
    
    def _has_embedded_scripts(self, content: bytes) -> bool:
        """Check for embedded scripts in file content"""
        script_patterns = [
            b'<script', b'javascript:', b'vbscript:', b'onload=', b'onerror=',
            b'<?php', b'<%', b'#!/bin/', b'#!/usr/bin/'
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in script_patterns)
    
    def _has_directory_traversal(self, filename: str) -> bool:
        """Check for directory traversal attempts"""
        traversal_patterns = ['../', '..\\', '%2e%2e%2f', '%2e%2e%5c', '....//']
        filename_lower = filename.lower()
        return any(pattern in filename_lower for pattern in traversal_patterns)
    
    def _perform_security_checks(self, file: FileStorage, filename: str) -> List[str]:
        """Perform additional security checks"""
        warnings = []
        
        # Check for suspicious filename patterns
        if re.search(r'\.(php|asp|jsp|py|rb|pl)\.(jpg|png|gif|bmp)$', filename.lower()):
            warnings.append("Filename has double extension pattern")
        
        # Check for very long filenames (potential buffer overflow)
        if len(filename) > 200:
            warnings.append("Filename is unusually long")
        
        # Check for Unicode normalization attacks
        if filename != filename.encode('utf-8').decode('utf-8'):
            warnings.append("Filename contains non-standard Unicode characters")
        
        return warnings
    
    def save_secure_file(self, file: FileStorage, subdirectory: str = 'images') -> FileInfo:
        """
        Save file securely with validation and protection
        
        Args:
            file: FileStorage object
            subdirectory: Subdirectory within upload directory
            
        Returns:
            FileInfo object with file details
            
        Raises:
            SecurityError: If file fails security validation
        """
        # Validate file first
        validation_result = self.validate_upload(file)
        if not validation_result.is_valid:
            raise SecurityError(f"File validation failed: {'; '.join(validation_result.errors)}")
        
        try:
            # Generate secure filename
            original_name = file.filename
            secure_name = self._generate_secure_filename(original_name)
            
            # Create target directory
            target_dir = self.upload_directory / subdirectory
            target_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate unique filename to prevent conflicts
            file_path = self._get_unique_filepath(target_dir / secure_name)
            
            # Save file
            file.save(str(file_path))
            
            # Get file information
            file_size = file_path.stat().st_size
            mime_type = validation_result.file_info.get('detected_mime_type', 'unknown')
            file_hash = self._calculate_file_hash(file_path)
            
            # Create file info
            file_info = FileInfo(
                original_name=original_name,
                secure_name=file_path.name,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                upload_time=datetime.utcnow()
            )
            
            logger.info(f"File saved securely: {original_name} -> {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise SecurityError(f"Failed to save file: {str(e)}")
    
    def _generate_secure_filename(self, filename: str) -> str:
        """Generate a secure filename"""
        # Use werkzeug's secure_filename as base
        secure_name = secure_filename(filename)
        
        # Additional sanitization
        secure_name = re.sub(r'[^\w\-_\.]', '_', secure_name)
        secure_name = re.sub(r'_{2,}', '_', secure_name)
        secure_name = secure_name.strip('_')
        
        # Ensure we have a valid filename
        if not secure_name or secure_name == '.':
            secure_name = f"file_{int(time.time())}"
        
        # Add timestamp to make it unique
        name_parts = secure_name.rsplit('.', 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            secure_name = f"{name}_{int(time.time())}.{ext}"
        else:
            secure_name = f"{secure_name}_{int(time.time())}"
        
        return secure_name
    
    def _get_unique_filepath(self, base_path: Path) -> Path:
        """Get unique filepath to prevent conflicts"""
        if not base_path.exists():
            return base_path
        
        # Add counter to make unique
        counter = 1
        while True:
            name_parts = base_path.name.rsplit('.', 1)
            if len(name_parts) == 2:
                name, ext = name_parts
                new_name = f"{name}_{counter}.{ext}"
            else:
                new_name = f"{base_path.name}_{counter}"
            
            new_path = base_path.parent / new_name
            if not new_path.exists():
                return new_path
            
            counter += 1
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate file hash: {e}")
            return ""
    
    def scan_for_malware(self, file_path: Path) -> bool:
        """
        Scan file for malware (basic implementation)
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            True if file is clean, False if suspicious
        """
        try:
            # Basic malware scanning - check file signatures
            with open(file_path, 'rb') as f:
                header = f.read(1024)
            
            # Check for malicious signatures
            for signature in self.MALICIOUS_SIGNATURES:
                if signature in header:
                    logger.warning(f"Malicious signature detected in {file_path}")
                    return False
            
            # Check file size (extremely large files might be suspicious)
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size * 2:  # Double the normal limit
                logger.warning(f"Suspiciously large file: {file_path} ({file_size} bytes)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Malware scanning error: {e}")
            return False  # Err on the side of caution
    
    def cleanup_temp_files(self, older_than: timedelta = timedelta(hours=24)) -> int:
        """
        Clean up temporary files older than specified time
        
        Args:
            older_than: Delete files older than this timedelta
            
        Returns:
            Number of files deleted
        """
        try:
            temp_dir = self.upload_directory / 'temp'
            if not temp_dir.exists():
                return 0
            
            deleted_count = 0
            cutoff_time = datetime.utcnow() - older_than
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if mod_time < cutoff_time:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            logger.info(f"Deleted old temp file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete temp file {file_path}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Temp file cleanup error: {e}")
            return 0
    
    def quarantine_file(self, file_path: Path, reason: str) -> bool:
        """
        Move suspicious file to quarantine directory
        
        Args:
            file_path: Path to file to quarantine
            reason: Reason for quarantine
            
        Returns:
            True if successful, False otherwise
        """
        try:
            quarantine_dir = self.upload_directory / 'quarantine'
            quarantine_dir.mkdir(exist_ok=True)
            
            # Generate quarantine filename with timestamp and reason
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            quarantine_name = f"{timestamp}_{file_path.name}"
            quarantine_path = quarantine_dir / quarantine_name
            
            # Move file to quarantine
            file_path.rename(quarantine_path)
            
            # Log quarantine action
            logger.warning(f"File quarantined: {file_path} -> {quarantine_path} (Reason: {reason})")
            
            # Create info file with quarantine details
            info_path = quarantine_path.with_suffix(quarantine_path.suffix + '.info')
            with open(info_path, 'w') as f:
                f.write(f"Original path: {file_path}\n")
                f.write(f"Quarantine time: {datetime.utcnow().isoformat()}\n")
                f.write(f"Reason: {reason}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"File quarantine error: {e}")
            return False
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive information about a file"""
        try:
            if not file_path.exists():
                return {"error": "File not found"}
            
            stat = file_path.stat()
            
            return {
                "name": file_path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "hash": self._calculate_file_hash(file_path),
                "is_safe": self.scan_for_malware(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {"error": str(e)}


# Global file handler instance
file_handler = FileHandler()