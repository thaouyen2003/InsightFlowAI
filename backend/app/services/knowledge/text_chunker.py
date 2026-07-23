from typing import Any

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


class TextChunker:
    """
    Chia tài liệu thành các đơn vị tri thức phục vụ RAG.

    Sử dụng RecursiveCharacterTextSplitter để ưu tiên:
    1. Đoạn văn
    2. Dòng
    3. Câu
    4. Khoảng trắng
    5. Ký tự
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size phải lớn hơn 0"
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap không được âm"
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap phải nhỏ hơn chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "; ",
                ", ",
                " ",
                "",
            ],
        )

    def split_document(
        self,
        document: dict[str, Any],
    ) -> list[dict[str, Any]]:
        content = str(
            document.get("content", "")
        ).strip()

        if not content:
            return []

        filename = str(
            document.get(
                "filename",
                "unknown_document",
            )
        )

        source = str(
            document.get(
                "source",
                filename,
            )
        )

        extension = str(
            document.get(
                "extension",
                "",
            )
        )

        texts = self.splitter.split_text(content)

        chunks: list[dict[str, Any]] = []

        for index, text in enumerate(texts):
            cleaned_text = text.strip()

            if not cleaned_text:
                continue

            chunks.append(
                {
                    "id": (
                        f"{self._safe_name(filename)}"
                        f"-chunk-{index + 1}"
                    ),
                    "text": cleaned_text,
                    "metadata": {
                        "filename": filename,
                        "source": source,
                        "extension": extension,
                        "chunk_index": index,
                        "chunk_number": index + 1,
                        "total_chunks": len(texts),
                        "character_count": len(
                            cleaned_text
                        ),
                    },
                }
            )

        return chunks

    def _safe_name(
        self,
        filename: str,
    ) -> str:
        safe_name = "".join(
            character
            if character.isalnum()
            else "-"
            for character in filename.lower()
        )

        return safe_name.strip("-")