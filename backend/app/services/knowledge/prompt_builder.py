from typing import Any


class KnowledgePromptBuilder:
    """
    Tạo prompt cho hệ thống RAG.

    Prompt kết hợp:
    - Câu hỏi người dùng
    - Tri thức truy xuất từ ChromaDB
    - Quy tắc trả lời có căn cứ
    """

    def build(
        self,
        query: str,
        knowledge_results: list[dict[str, Any]],
    ) -> str:
        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "Câu hỏi không được để trống"
            )

        context = self._build_context(
            knowledge_results
        )

        return f"""
Bạn là trợ lý quản lý tri thức giáo dục của hệ thống
InsightFlowAI.

Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các đoạn
tri thức được cung cấp bên dưới.

QUY TẮC BẮT BUỘC:

1. Chỉ sử dụng thông tin có trong phần TRI THỨC TRUY XUẤT.
2. Không tự tạo quy định, số liệu hoặc nguồn tài liệu.
3. Nếu tri thức chưa đủ, phải nói rõ rằng chưa đủ căn cứ.
4. Câu trả lời phải ngắn gọn, rõ ràng và phù hợp với
   bối cảnh quản lý giáo dục.
5. Phải nêu nguồn tài liệu đã sử dụng.
6. Khuyến nghị phải được suy ra từ tri thức truy xuất,
   không được khẳng định như một quy định chính thức
   nếu tài liệu không nói rõ.

CÂU HỎI:

{cleaned_query}

TRI THỨC TRUY XUẤT:

{context}

Hãy trả lời đúng cấu trúc sau:

## Kết luận
Trả lời trực tiếp câu hỏi.

## Tri thức liên quan
Tóm tắt những nội dung quan trọng được tìm thấy.

## Khuyến nghị
Đề xuất hành động phù hợp dựa trên tri thức đã truy xuất.

## Nguồn
Liệt kê tên tài liệu và số chunk đã sử dụng.
""".strip()

    def _build_context(
        self,
        knowledge_results: list[dict[str, Any]],
    ) -> str:
        if not knowledge_results:
            return (
                "Không tìm thấy đoạn tri thức phù hợp "
                "trong Knowledge Base."
            )

        context_parts: list[str] = []

        for index, result in enumerate(
            knowledge_results,
            start=1,
        ):
            content = str(
                result.get("content", "")
            ).strip()

            metadata = result.get(
                "metadata",
                {},
            )

            if not isinstance(metadata, dict):
                metadata = {}

            filename = metadata.get(
                "filename",
                "Không rõ nguồn",
            )

            chunk_number = metadata.get(
                "chunk_number",
                "Không xác định",
            )

            source = metadata.get(
                "source",
                filename,
            )

            context_parts.append(
                "\n".join(
                    [
                        f"[TRI THỨC {index}]",
                        f"Tài liệu: {filename}",
                        f"Chunk: {chunk_number}",
                        f"Nguồn: {source}",
                        "Nội dung:",
                        content,
                    ]
                )
            )

        return "\n\n".join(context_parts)