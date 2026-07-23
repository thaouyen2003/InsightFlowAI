from typing import Any

from pydantic import BaseModel, Field

from app.services.rag.document_loader import (
    LoadedDocument,
)


class KnowledgeChunk(BaseModel):
    """
    Một đoạn tri thức nhỏ được chia từ tài liệu PDF.
    """

    id: str

    content: str

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class TextChunker:
    """
    Chia nội dung tài liệu thành các đoạn nhỏ,
    có phần chồng lấn để giữ ngữ cảnh.
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size phải lớn hơn 0."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap không được âm."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap phải nhỏ hơn chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_documents(
        self,
        documents: list[LoadedDocument],
    ) -> list[KnowledgeChunk]:
        """
        Chia toàn bộ danh sách tài liệu thành chunks.
        """

        chunks: list[KnowledgeChunk] = []

        for document_index, document in enumerate(
            documents,
            start=1,
        ):
            document_chunks = self._chunk_text(
                document.content
            )

            for chunk_index, content in enumerate(
                document_chunks,
                start=1,
            ):
                metadata = dict(
                    document.metadata
                )

                metadata.update(
                    {
                        "document_index": document_index,
                        "chunk_index": chunk_index,
                    }
                )

                chunk_id = self._build_chunk_id(
                    metadata=metadata,
                    document_index=document_index,
                    chunk_index=chunk_index,
                )

                chunks.append(
                    KnowledgeChunk(
                        id=chunk_id,
                        content=content,
                        metadata=metadata,
                    )
                )

        return chunks

 
    def _chunk_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Chia văn bản theo từ hoàn chỉnh.

        Không cắt giữa từ và tạo overlap
        bằng các từ hoàn chỉnh.
        """

        normalized_text = " ".join(
            text.split()
        ).strip()

        if not normalized_text:
            return []

        if len(normalized_text) <= self.chunk_size:
            return [normalized_text]

        words = normalized_text.split()
        chunks: list[str] = []

        start_word = 0
        total_words = len(words)

        while start_word < total_words:
            end_word = start_word
            current_length = 0

            while end_word < total_words:
                word = words[end_word]

                additional_length = len(word)

                if end_word > start_word:
                    additional_length += 1

                if (
                    current_length + additional_length
                    > self.chunk_size
                ):
                    break

                current_length += additional_length
                end_word += 1

            if end_word == start_word:
                end_word = start_word + 1

            chunk = " ".join(
                words[start_word:end_word]
            ).strip()

            if chunk:
                chunks.append(chunk)

            if end_word >= total_words:
                break

            overlap_start = end_word
            overlap_length = 0

            while overlap_start > start_word:
                previous_word = words[
                    overlap_start - 1
                ]

                additional_length = len(
                    previous_word
                )

                if overlap_length > 0:
                    additional_length += 1

                if (
                    overlap_length + additional_length
                    > self.chunk_overlap
                ):
                    break

                overlap_start -= 1
                overlap_length += additional_length

            if overlap_start <= start_word:
                start_word = end_word
            else:
                start_word = overlap_start

        return chunks

    def _build_chunk_id(
        self,
        metadata: dict[str, Any],
        document_index: int,
        chunk_index: int,
    ) -> str:
        source = str(
            metadata.get(
                "source",
                "document",
            )
        )

        page = metadata.get(
            "page",
            document_index,
        )

        safe_source = "".join(
            character
            if character.isalnum()
            else "_"
            for character in source
        )

        return (
            f"{safe_source}"
            f"_page_{page}"
            f"_chunk_{chunk_index}"
        )