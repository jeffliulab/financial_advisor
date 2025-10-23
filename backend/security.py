"""
Security utilities for file access control.
"""
import os
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from models import File, User

def verify_file_access(file_id: str, user_id: str, db: Session) -> Optional[File]:
    """
    Verify that a user has access to a specific file.
    Returns the file object if access is granted, None otherwise.
    """
    file_record = db.query(File).filter(
        File.id == file_id,
        File.user_id == user_id
    ).first()
    
    return file_record

def sanitize_file_path(file_path: str) -> bool:
    """
    Sanitize file path to prevent directory traversal attacks.
    Returns True if path is safe, False otherwise.
    """
    # Convert to absolute path
    abs_path = os.path.abspath(file_path)
    
    # Check if path is within allowed directory
    allowed_dir = os.path.abspath("/app/data/secure_uploads")
    
    # Ensure the file is within the allowed directory
    return abs_path.startswith(allowed_dir)

def get_file_with_access_check(file_id: str, user_id: str, db: Session) -> Optional[dict]:
    """
    Get file information with access control check.
    Returns file info dict if access is granted, None otherwise.
    """
    file_record = verify_file_access(file_id, user_id, db)
    
    if not file_record:
        return None
    
    # Verify file path is safe
    if not sanitize_file_path(file_record.file_path):
        return None
    
    # Check if file exists on disk
    if not os.path.exists(file_record.file_path):
        return None
    
    return {
        'id': file_record.id,
        'filename': file_record.filename,
        'secure_filename': file_record.secure_filename,
        'file_path': file_record.file_path,
        'file_size': file_record.file_size,
        'file_type': file_record.file_type,
        'upload_time': file_record.upload_time.isoformat()
    }

def cleanup_insecure_files():
    """
    Clean up any files that might be stored in insecure locations.
    This is a maintenance function.
    """
    # Remove any files in the old insecure upload directory
    old_upload_dir = Path("/app/data/uploads")
    if old_upload_dir.exists():
        import shutil
        shutil.rmtree(old_upload_dir, ignore_errors=True)
