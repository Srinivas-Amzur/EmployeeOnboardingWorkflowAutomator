"""
Document service for managing onboarding documents and files.
"""

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import os


class DocumentService:
    """Service for managing onboarding documents."""

    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, base_upload_dir: str = "./uploads"):
        """
        Initialize document service.

        Args:
            base_upload_dir: Base directory for file uploads
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str, file_size: int) -> tuple[bool, str]:
        """
        Validate if file is acceptable.

        Args:
            filename: Name of the file
            file_size: Size of the file in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum of {self.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"

        return True, ""

    def get_upload_path(self, workflow_id: UUID) -> Path:
        """
        Get the upload path for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Path object for the workflow directory
        """
        workflow_dir = self.base_upload_dir / str(workflow_id)
        workflow_dir.mkdir(parents=True, exist_ok=True)
        return workflow_dir

    def save_file(
        self,
        workflow_id: UUID,
        file_content: bytes,
        original_filename: str,
        document_type: str = "general",
    ) -> dict:
        """
        Save an uploaded file.

        Args:
            workflow_id: Workflow ID
            file_content: File content as bytes
            original_filename: Original filename
            document_type: Type of document (e.g., "offer_letter", "agreement")

        Returns:
            File metadata dictionary
        """
        # Validate file
        is_valid, error_msg = self.validate_file(original_filename, len(file_content))
        if not is_valid:
            raise ValueError(error_msg)

        # Generate safe filename
        file_id = uuid4()
        file_ext = Path(original_filename).suffix.lower()
        safe_filename = f"{file_id}{file_ext}"

        # Save file
        upload_path = self.get_upload_path(workflow_id)
        file_path = upload_path / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        file_metadata = {
            "file_id": str(file_id),
            "workflow_id": str(workflow_id),
            "original_filename": original_filename,
            "safe_filename": safe_filename,
            "file_path": str(file_path),
            "document_type": document_type,
            "file_size": len(file_content),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "mime_type": self.get_mime_type(original_filename),
        }

        return file_metadata

    def get_file(self, workflow_id: UUID, file_id: str) -> tuple[bytes, str] | None:
        """
        Retrieve a file.

        Args:
            workflow_id: Workflow ID
            file_id: File ID

        Returns:
            Tuple of (file_content, original_filename) or None if not found
        """
        upload_path = self.get_upload_path(workflow_id)

        # Find file with matching ID prefix
        for file_path in upload_path.glob(f"{file_id}*"):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    return f.read(), f"{file_id}{file_path.suffix}"

        return None

    def delete_file(self, workflow_id: UUID, file_id: str) -> bool:
        """
        Delete a file.

        Args:
            workflow_id: Workflow ID
            file_id: File ID

        Returns:
            True if deleted, False if not found
        """
        upload_path = self.get_upload_path(workflow_id)

        # Find and delete file with matching ID prefix
        for file_path in upload_path.glob(f"{file_id}*"):
            if file_path.is_file():
                file_path.unlink()
                return True

        return False

    def list_workflow_files(self, workflow_id: UUID) -> list[dict]:
        """
        List all files for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of file metadata dictionaries
        """
        upload_path = self.get_upload_path(workflow_id)
        files = []

        for file_path in upload_path.glob("*"):
            if file_path.is_file():
                files.append(
                    {
                        "file_id": file_path.stem,
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "uploaded_at": datetime.fromtimestamp(
                            file_path.stat().st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )

        return sorted(files, key=lambda x: x["uploaded_at"], reverse=True)

    def get_mime_type(self, filename: str) -> str:
        """
        Get MIME type for a file.

        Args:
            filename: Name of the file

        Returns:
            MIME type string
        """
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mime_types.get(ext, "application/octet-stream")

    def cleanup_old_files(self, workflow_id: UUID, days_old: int = 30) -> int:
        """
        Clean up old files for a workflow.

        Args:
            workflow_id: Workflow ID
            days_old: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        from datetime import timedelta

        upload_path = self.get_upload_path(workflow_id)
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
        deleted_count = 0

        for file_path in upload_path.glob("*"):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(
                    file_path.stat().st_mtime, tz=timezone.utc
                )
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1

        return deleted_count
