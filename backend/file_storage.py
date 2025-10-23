"""
File storage utilities for handling user uploads.
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session
from models import File, User, ChatSession
import mimetypes

# File storage configuration
UPLOAD_BASE_DIR = "/app/data/uploads"
SECURE_UPLOAD_DIR = "/app/data/secure_uploads"  # 更安全的存储目录
ALLOWED_EXTENSIONS = {
    'images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'},
    'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'},
    'spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
    'presentations': {'.ppt', '.pptx', '.odp'},
    'archives': {'.zip', '.rar', '.7z', '.tar', '.gz'}
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_file_category(filename: str) -> str:
    """Determine file category based on extension."""
    ext = Path(filename).suffix.lower()
    
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    
    return 'other'

def is_allowed_file(filename: str) -> bool:
    """Check if file type is allowed."""
    ext = Path(filename).suffix.lower()
    all_allowed = set()
    for extensions in ALLOWED_EXTENSIONS.values():
        all_allowed.update(extensions)
    return ext in all_allowed

def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)

def get_mime_type(filename: str) -> str:
    """Get MIME type for file."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def create_secure_directory() -> str:
    """Create secure directory for file uploads (no user ID in path)."""
    secure_dir = Path(SECURE_UPLOAD_DIR)
    secure_dir.mkdir(parents=True, exist_ok=True)
    return str(secure_dir)

def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename that doesn't reveal user information."""
    import hashlib
    import time
    
    # Create a hash based on filename + timestamp + random
    timestamp = str(int(time.time() * 1000))
    random_part = str(uuid.uuid4())[:8]
    file_ext = Path(original_filename).suffix.lower()
    
    # Create hash
    hash_input = f"{original_filename}{timestamp}{random_part}"
    file_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    return f"{file_hash}{file_ext}"

def save_uploaded_file(file_content: bytes, filename: str, user_id: str, session_id: Optional[str] = None) -> dict:
    """Save uploaded file and return file info."""
    # Validate file
    if not is_allowed_file(filename):
        raise ValueError(f"File type not allowed: {filename}")
    
    # Check file size before saving
    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {len(file_content)} bytes (max: {MAX_FILE_SIZE})")
    
    # Create secure directory
    secure_dir = create_secure_directory()
    
    # Generate secure filename and file ID
    file_id = str(uuid.uuid4())
    secure_filename = generate_secure_filename(filename)
    
    # Save file with secure filename
    file_path = Path(secure_dir) / secure_filename
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # Get file info
    file_size = get_file_size(str(file_path))
    
    file_info = {
        'id': file_id,
        'user_id': user_id,
        'session_id': session_id,
        'filename': filename,  # Original filename for display
        'secure_filename': secure_filename,  # Secure filename for storage
        'file_path': str(file_path),
        'file_size': file_size,
        'file_type': get_mime_type(filename),
        'category': get_file_category(filename)
    }
    
    return file_info

def delete_file(file_path: str) -> bool:
    """Delete file from filesystem."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False

def get_user_files(db: Session, user_id: str, session_id: Optional[str] = None) -> List[dict]:
    """Get files for a user, optionally filtered by session."""
    query = db.query(File).filter(File.user_id == user_id)
    
    if session_id:
        query = query.filter(File.session_id == session_id)
    
    files = query.order_by(File.upload_time.desc()).all()
    
    return [
        {
            'id': file.id,
            'filename': file.filename,
            'file_size': file.file_size,
            'file_type': file.file_type,
            'upload_time': file.upload_time.isoformat(),
            'category': get_file_category(file.filename)
        }
        for file in files
    ]

def cleanup_orphaned_files(db: Session) -> int:
    """Clean up files that are no longer referenced in database."""
    # This is a utility function for maintenance
    # Implementation would scan filesystem and remove files not in database
    pass
