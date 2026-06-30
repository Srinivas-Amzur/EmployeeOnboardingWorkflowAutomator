"""Document processing service for RAG ingestion."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - compatibility with older langchain installs
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from ..core.config import get_settings

settings = get_settings()


class DocumentProcessingService:
    """Validates, stores, extracts, and chunks onboarding documents."""

    _ALLOWED_MIME_TYPES = {
        "application/pdf",
    }
    _ALLOWED_EXTENSIONS = {".pdf"}

    def __init__(self) -> None:
        self.upload_root = Path(settings.UPLOAD_DIR) / "rag"
        self.upload_root.mkdir(parents=True, exist_ok=True)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=220,
            separators=["\n\n", "\n", ". ", " "],
        )

    def _user_dir(self, user_id: UUID) -> Path:
        path = self.upload_root / f"user_{user_id}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _validate_upload(self, upload_file: UploadFile, byte_count: int) -> None:
        extension = Path(upload_file.filename or "").suffix.lower()
        if extension not in self._ALLOWED_EXTENSIONS:
            raise ValueError("Only PDF documents are supported for RAG ingestion")

        if upload_file.content_type not in self._ALLOWED_MIME_TYPES:
            raise ValueError("Invalid MIME type. Expected application/pdf")

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if byte_count > max_size:
            raise ValueError(f"File exceeds max size of {settings.MAX_UPLOAD_SIZE_MB}MB")

    def _extract_pdf_text(self, file_path: Path) -> str:
        reader = PdfReader(str(file_path))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        content = "\n".join(pages).strip()
        if not content:
            raise ValueError("Unable to extract text from PDF")
        return content

    async def process_upload(self, user_id: UUID, upload_file: UploadFile) -> dict:
        """Persist file, extract text, and return chunks + metadata."""
        file_bytes = await upload_file.read()
        self._validate_upload(upload_file, len(file_bytes))

        document_id = str(uuid4())
        extension = Path(upload_file.filename or "document.pdf").suffix.lower() or ".pdf"
        file_name = f"{document_id}{extension}"
        file_path = self._user_dir(user_id) / file_name
        file_path.write_bytes(file_bytes)

        content = self._extract_pdf_text(file_path)
        chunks = [chunk.strip() for chunk in self.text_splitter.split_text(content) if chunk.strip()]
        if not chunks:
            raise ValueError("Document text extraction succeeded but no chunks were generated")

        return {
            "document_id": document_id,
            "document_name": upload_file.filename or file_name,
            "content": content,
            "chunks": chunks,
            "file_path": str(file_path),
            "mime_type": upload_file.content_type,
            "file_size": len(file_bytes),
        }
