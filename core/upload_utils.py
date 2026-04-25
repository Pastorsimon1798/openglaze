"""
Upload utilities for OpenGlaze.
File validation, saving, and path management.
"""

import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str) -> bool:
    """Check if file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file, upload_folder: str) -> str:
    """
    Save an uploaded file with a secure filename.
    Returns the relative path from the frontend root (e.g., 'uploads/filename.jpg').
    Raises ValueError for invalid files, OverflowError for oversized files.
    """
    if not file or not file.filename:
        raise ValueError("No file provided")

    if not allowed_file(file.filename):
        raise ValueError(f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}")

    # Check file size
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
    except Exception:
        raise ValueError("Could not read file")

    if size > MAX_FILE_SIZE:
        raise OverflowError(
            f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    # Avoid collisions by prepending timestamp
    import time

    name, ext = os.path.splitext(filename)
    filename = f"{name}-{int(time.time())}{ext}"

    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)

    return f"uploads/{filename}"
