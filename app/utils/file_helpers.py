"""
File validation and handling utilities.
"""
import os
from typing import Tuple
from fastapi import UploadFile

from app.core.config import settings
from app.utils.logger import logger


def validate_file_type(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate if the uploaded file type is allowed.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not file:
        return False, "No file provided"
    
    # Check content type
    allowed_types = settings.allowed_file_types_list
    if file.content_type not in allowed_types:
        return False, f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
    
    # Check file extension
    if not file.filename.lower().endswith('.pdf'):
        return False, "Only PDF files are allowed"
    
    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate if file size is within limits.
    
    Args:
        file_size: Size in bytes
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    max_size = settings.max_file_size_bytes
    
    if file_size > max_size:
        max_mb = settings.max_file_size_mb
        actual_mb = file_size / (1024 * 1024)
        return False, f"File size {actual_mb:.2f}MB exceeds maximum allowed size of {max_mb}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, ""


async def read_upload_file(file: UploadFile) -> bytes:
    """
    Read uploaded file contents.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        File contents as bytes
    """
    try:
        contents = await file.read()
        # Reset file pointer for potential re-reads
        await file.seek(0)
        return contents
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise


def get_file_size(contents: bytes) -> int:
    """
    Get size of file contents in bytes.
    
    Args:
        contents: File contents as bytes
        
    Returns:
        Size in bytes
    """
    return len(contents)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any directory path components
    filename = os.path.basename(filename)
    
    # Replace unsafe characters
    unsafe_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename
