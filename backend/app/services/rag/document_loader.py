from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pypdf import PdfReader


class LoadedDocument(BaseModel):
    """
    Đại diện cho nội dung của một trang PDF
    đã được đọc từ Knowledge Base.
    """

    content: str

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class DocumentLoader:
    """
    Đọc toàn bộ tài liệu PDF trong Knowledge Base VHU.
    """

    def __init__(
        self,
        knowledge_base_dir: str | Path | None = None,
    ) -> None:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        self.knowledge_base_dir = (
            Path(knowledge_base_dir)
            if knowledge_base_dir
            else backend_dir / "knowledge_base"
        )

    def load_all(
        self,
    ) -> list[LoadedDocument]:
        """
        Đọc toàn bộ file PDF trong knowledge_base.
        """

        if not self.knowledge_base_dir.exists():
            raise FileNotFoundError(
                "Không tìm thấy thư mục knowledge_base: "
                f"{self.knowledge_base_dir}"
            )

        documents: list[LoadedDocument] = []

        pdf_paths = sorted(
            self.knowledge_base_dir.rglob("*.pdf")
        )

        for pdf_path in pdf_paths:
            documents.extend(
                self._load_pdf(pdf_path)
            )

        return documents

    def _load_pdf(
        self,
        pdf_path: Path,
    ) -> list[LoadedDocument]:
        """
        Đọc từng trang trong một file PDF.
        """

        category = pdf_path.parent.name

        try:
            reader = PdfReader(
                str(pdf_path)
            )
        except Exception as error:
            print(
                "Không thể đọc PDF:",
                pdf_path.name,
                str(error),
            )
            return []

        documents: list[LoadedDocument] = []

        for page_index, page in enumerate(
            reader.pages,
            start=1,
        ):
            try:
                text = page.extract_text() or ""
            except Exception as error:
                print(
                    "Không thể đọc trang:",
                    pdf_path.name,
                    page_index,
                    str(error),
                )
                continue

            normalized_text = self._normalize_text(
                text
            )

            if not normalized_text:
                continue

            documents.append(
                LoadedDocument(
                    content=normalized_text,
                    metadata={
                        "category": category,
                        "source": pdf_path.name,
                        "page": page_index,
                        "path": str(
                            pdf_path.relative_to(
                                self.knowledge_base_dir
                            )
                        ),
                    },
                )
            )

        return documents

    def _normalize_text(
        self,
        text: str,
    ) -> str:
        """
        Chuẩn hóa khoảng trắng trong văn bản.
        """

        lines = [
            " ".join(line.split())
            for line in text.splitlines()
        ]

        lines = [
            line
            for line in lines
            if line
        ]

        return "\n".join(lines).strip()