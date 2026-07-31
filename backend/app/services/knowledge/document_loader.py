from pathlib import Path

from docx import Document
from pypdf import PdfReader


class DocumentLoader:
    """
    Đọc tài liệu phục vụ Knowledge Base.

    Hỗ trợ:
    - PDF
    - DOCX
    - TXT
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    def load(self, file_path: str | Path) -> dict:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy tài liệu: {path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Định dạng chưa được hỗ trợ: {extension}"
            )

        if extension == ".pdf":
            content = self._read_pdf(path)
        elif extension == ".docx":
            content = self._read_docx(path)
        else:
            content = self._read_txt(path)

        content = self._normalize_text(content)

        return {
            "filename": path.name,
            "source": str(path),
            "extension": extension,
            "content": content,
            "character_count": len(content),
        }

    def _read_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages: list[str] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            text = page.extract_text() or ""

            if text.strip():
                pages.append(
                    f"[Trang {page_number}]\n{text}"
                )

        return "\n\n".join(pages)

    def _read_docx(self, path: Path) -> str:
        document = Document(str(path))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n\n".join(paragraphs)

    def _read_txt(self, path: Path) -> str:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    def _normalize_text(self, text: str) -> str:
        lines = [
            line.strip()
            for line in text.splitlines()
        ]

        cleaned_lines: list[str] = []
        previous_empty = False

        for line in lines:
            is_empty = not line

            if is_empty and previous_empty:
                continue

            cleaned_lines.append(line)
            previous_empty = is_empty

        return "\n".join(cleaned_lines).strip()