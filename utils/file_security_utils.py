"""
File Security Utilities

Additional utilities for file security, testing, and management.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from werkzeug.datastructures import FileStorage
from io import BytesIO
import sys

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.file_handler import file_handler, ValidationResult, SecurityError

logger = logging.getLogger(__name__)


class FileSecurityTester:
    """Utility class for testing file security features"""
    
    @staticmethod
    def create_test_image(filename: str = "test.jpg", size: int = 1024) -> FileStorage:
        """Create a test image file for testing"""
        # Create a minimal JPEG header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
        jpeg_data = jpeg_header + b'\x00' * (size - len(jpeg_header)) + b'\xff\xd9'
        
        file_obj = BytesIO(jpeg_data)
        return FileStorage(
            stream=file_obj,
            filename=filename,
            content_type='image/jpeg'
        )
    
    @staticmethod
    def create_malicious_file(filename: str = "malicious.jpg") -> FileStorage:
        """Create a file with malicious content for testing"""
        # PE executable header disguised as image
        malicious_data = b'\x4d\x5a' + b'\x00' * 1022  # PE header + padding
        
        file_obj = BytesIO(malicious_data)
        return FileStorage(
            stream=file_obj,
            filename=filename,
            content_type='image/jpeg'
        )
    
    @staticmethod
    def create_oversized_file(filename: str = "large.jpg", size: int = None) -> FileStorage:
        """Create an oversized file for testing"""
        if size is None:
            size = file_handler.max_file_size + 1024  # Slightly over limit
        
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
        large_data = jpeg_header + b'\x00' * (size - len(jpeg_header) - 2) + b'\xff\xd9'
        
        file_obj = BytesIO(large_data)
        return FileStorage(
            stream=file_obj,
            filename=filename,
            content_type='image/jpeg'
        )
    
    @staticmethod
    def test_file_validation() -> Dict[str, Any]:
        """Test file validation with various scenarios"""
        results = {}
        
        # Test valid file
        try:
            valid_file = FileSecurityTester.create_test_image("valid.jpg")
            result = file_handler.validate_upload(valid_file)
            results['valid_file'] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings
            }
        except Exception as e:
            results['valid_file'] = {'error': str(e)}
        
        # Test malicious file
        try:
            malicious_file = FileSecurityTester.create_malicious_file("malicious.jpg")
            result = file_handler.validate_upload(malicious_file)
            results['malicious_file'] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings
            }
        except Exception as e:
            results['malicious_file'] = {'error': str(e)}
        
        # Test oversized file
        try:
            oversized_file = FileSecurityTester.create_oversized_file("large.jpg")
            result = file_handler.validate_upload(oversized_file)
            results['oversized_file'] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings
            }
        except Exception as e:
            results['oversized_file'] = {'error': str(e)}
        
        # Test dangerous extension
        try:
            dangerous_file = FileSecurityTester.create_test_image("script.php.jpg")
            result = file_handler.validate_upload(dangerous_file)
            results['dangerous_extension'] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings
            }
        except Exception as e:
            results['dangerous_extension'] = {'error': str(e)}
        
        # Test directory traversal
        try:
            traversal_file = FileSecurityTester.create_test_image("../../../etc/passwd.jpg")
            result = file_handler.validate_upload(traversal_file)
            results['directory_traversal'] = {
                'is_valid': result.is_valid,
                'errors': result.errors,
                'warnings': result.warnings
            }
        except Exception as e:
            results['directory_traversal'] = {'error': str(e)}
        
        return results


class FileSystemMonitor:
    """Monitor file system for security events"""
    
    def __init__(self):
        self.upload_directory = file_handler.upload_directory
    
    def scan_upload_directory(self) -> Dict[str, Any]:
        """Scan upload directory for security issues"""
        results = {
            'total_files': 0,
            'suspicious_files': [],
            'large_files': [],
            'old_files': [],
            'quarantined_files': 0
        }
        
        try:
            # Scan all files in upload directory
            for file_path in self.upload_directory.rglob('*'):
                if file_path.is_file():
                    results['total_files'] += 1
                    
                    # Check file info
                    file_info = file_handler.get_file_info(file_path)
                    
                    # Check if file is suspicious
                    if not file_info.get('is_safe', True):
                        results['suspicious_files'].append({
                            'path': str(file_path),
                            'reason': 'Failed malware scan'
                        })
                    
                    # Check for large files
                    file_size = file_info.get('size', 0)
                    if file_size > file_handler.max_file_size:
                        results['large_files'].append({
                            'path': str(file_path),
                            'size': file_size
                        })
            
            # Count quarantined files
            quarantine_dir = self.upload_directory / 'quarantine'
            if quarantine_dir.exists():
                results['quarantined_files'] = len(list(quarantine_dir.glob('*')))
        
        except Exception as e:
            logger.error(f"Directory scan error: {e}")
            results['error'] = str(e)
        
        return results
    
    def cleanup_old_files(self, days: int = 30) -> Dict[str, Any]:
        """Clean up old files from upload directory"""
        from datetime import datetime, timedelta
        
        results = {
            'deleted_files': 0,
            'errors': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for file_path in self.upload_directory.rglob('*'):
                if file_path.is_file():
                    # Skip quarantine directory
                    if 'quarantine' in file_path.parts:
                        continue
                    
                    try:
                        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mod_time < cutoff_date:
                            file_path.unlink()
                            results['deleted_files'] += 1
                            logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        results['errors'].append(f"Failed to delete {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            results['error'] = str(e)
        
        return results


class FileUploadHelper:
    """Helper class for handling file uploads in routes"""
    
    @staticmethod
    def process_upload(file: FileStorage, subdirectory: str = 'images') -> Dict[str, Any]:
        """
        Process file upload with comprehensive error handling
        
        Args:
            file: FileStorage object from request
            subdirectory: Target subdirectory
            
        Returns:
            Dictionary with upload result
        """
        try:
            # Validate file
            validation_result = file_handler.validate_upload(file)
            
            if not validation_result.is_valid:
                return {
                    'success': False,
                    'error': 'File validation failed',
                    'details': validation_result.errors,
                    'warnings': validation_result.warnings
                }
            
            # Save file securely
            file_info = file_handler.save_secure_file(file, subdirectory)
            
            # Perform malware scan
            is_safe = file_handler.scan_for_malware(file_info.file_path)
            
            if not is_safe:
                # Quarantine suspicious file
                file_handler.quarantine_file(
                    file_info.file_path, 
                    "Failed malware scan"
                )
                return {
                    'success': False,
                    'error': 'File failed security scan',
                    'details': ['File has been quarantined for security reasons']
                }
            
            return {
                'success': True,
                'file_info': {
                    'original_name': file_info.original_name,
                    'secure_name': file_info.secure_name,
                    'file_path': str(file_info.file_path),
                    'file_size': file_info.file_size,
                    'mime_type': file_info.mime_type,
                    'upload_time': file_info.upload_time.isoformat()
                },
                'warnings': validation_result.warnings
            }
        
        except SecurityError as e:
            logger.warning(f"Security error during upload: {e}")
            return {
                'success': False,
                'error': 'Security validation failed',
                'details': [str(e)]
            }
        
        except Exception as e:
            logger.error(f"Upload processing error: {e}")
            return {
                'success': False,
                'error': 'Upload processing failed',
                'details': [str(e)]
            }
    
    @staticmethod
    def get_upload_status() -> Dict[str, Any]:
        """Get current upload system status"""
        try:
            monitor = FileSystemMonitor()
            scan_results = monitor.scan_upload_directory()
            
            return {
                'upload_directory': str(file_handler.upload_directory),
                'allowed_extensions': list(file_handler.allowed_extensions),
                'max_file_size': file_handler.max_file_size,
                'directory_scan': scan_results
            }
        
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                'error': str(e)
            }


# Global instances
security_tester = FileSecurityTester()
file_monitor = FileSystemMonitor()
upload_helper = FileUploadHelper()