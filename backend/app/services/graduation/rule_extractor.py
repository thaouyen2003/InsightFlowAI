from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from app.services.graduation.rule_schema import (
    GraduationRuleSchema,
)
from app.services.graduation.rule_validator import (
    GraduationRuleValidator,
)
from app.services.graduation.rules import (
    GraduationRuleSet,
)


class GraduationRuleExtractionError(
    RuntimeError
):
    """
    Lỗi khi không thể trích xuất bộ luật hợp lệ.
    """


class GraduationRuleExtractor:
    """
    Chuyển các đoạn tri thức do RAG truy xuất
    thành GraduationRuleSet có cấu trúc.

    Hàm generate_text được truyền từ bên ngoài,
    giúp extractor không phụ thuộc trực tiếp vào
    Gemini hoặc OpenRouter.
    """

    def __init__(
        self,
        generate_text: Callable[[str], str],
    ) -> None:
        self.generate_text = generate_text

    @staticmethod
    def _build_field_description() -> str:
        """
        Tạo mô tả danh sách field được phép sử dụng.
        """

        lines: list[str] = []

        for (
            field_name,
            description,
        ) in (
            GraduationRuleSchema
            .FIELD_DESCRIPTIONS.items()
        ):
            lines.append(
                f"- {field_name}: {description}"
            )

        return "\n".join(lines)

    @classmethod
    def build_prompt(
        cls,
        *,
        retrieved_chunks: list[
            dict[str, Any]
        ],
        major: str | None = None,
        cohort: str | None = None,
    ) -> str:
        """
        Tạo prompt trích xuất luật từ các chunk
        được lấy từ kho tri thức.
        """

        context_blocks: list[str] = []

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):
            document_name = str(
                chunk.get(
                    "document_name",
                    chunk.get(
                        "source",
                        "unknown.pdf",
                    ),
                )
            )

            page_number = chunk.get(
                "page_number",
                chunk.get("page"),
            )

            chunk_id = chunk.get(
                "chunk_id",
                f"chunk_{index}",
            )

            content = str(
                chunk.get(
                    "content",
                    chunk.get(
                        "text",
                        "",
                    ),
                )
            ).strip()

            context_blocks.append(
                "\n".join(
                    [
                        f"[CHUNK {index}]",
                        (
                            "document_name: "
                            f"{document_name}"
                        ),
                        (
                            "page_number: "
                            f"{page_number}"
                        ),
                        f"chunk_id: {chunk_id}",
                        "content:",
                        content,
                    ]
                )
            )

        context = "\n\n".join(
            context_blocks
        )

        field_description = (
            cls._build_field_description()
        )

        return f"""
Bạn là hệ thống trích xuất tri thức quy chế
xét tốt nghiệp.

Nhiệm vụ:
Chuyển các điều kiện tốt nghiệp xuất hiện rõ ràng
trong tài liệu thành JSON có cấu trúc.

Ngành được yêu cầu:
{major or "Không xác định"}

Khóa được yêu cầu:
{cohort or "Không xác định"}

Chỉ được sử dụng các field_name sau:

{field_description}

Operator hợp lệ:

- greater_than_or_equal
- less_than_or_equal
- equal
- not_equal
- in
- not_in

Quy tắc bắt buộc:

1. Không tự suy diễn điều kiện không có trong tài liệu.
2. Không tự đặt ngưỡng điểm hoặc số tín chỉ.
3. Mỗi luật phải có document_name, page_number,
   chunk_id và evidence_text.
4. evidence_text phải là đoạn ngắn lấy từ nội dung
   được cung cấp.
5. Nếu tài liệu không nêu rõ một điều kiện thì
   không tạo luật đó.
6. Nếu điều kiện phụ thuộc ngành hoặc khóa, phải
   phản ánh trong major hoặc cohort.
7. confidence phải nằm trong khoảng từ 0 đến 1.
8. Chỉ trả về JSON, không dùng Markdown.
9. Với operator "in" hoặc "not_in",
   accepted_values phải có ít nhất một giá trị.
10. Không được tạo luật có dạng:

    "operator": "in",
    "accepted_values": []

    hoặc:

    "operator": "not_in",
    "accepted_values": []

11. Nếu tài liệu không nêu rõ các giá trị cho phép
    hoặc các giá trị bị loại trừ thì không tạo luật đó.
12. Với các operator số như greater_than_or_equal
    hoặc less_than_or_equal, required_value phải
    chứa giá trị số phù hợp.
13. Không đưa cùng một điều kiện vào nhiều luật
    trùng lặp.

JSON phải có cấu trúc:

{{
  "rule_set_code": "string",
  "rule_set_name": "string",
  "version": "1.0",
  "major": null,
  "cohort": null,
  "program": null,
  "effective_date": null,
  "source_documents": [
    "document.pdf"
  ],
  "extraction_notes": [],
  "generated_by": "rag_rule_extractor",
  "rules": [
    {{
      "code": "minimum_gpa",
      "name": "Điểm trung bình tích lũy",
      "field_name": "gpa",
      "operator": "greater_than_or_equal",
      "required_value": 2.0,
      "accepted_values": [],
      "failure_message": "Điểm trung bình chưa đạt.",
      "recommendation": "Cần học cải thiện.",
      "is_required": true,
      "confidence": 0.95,
      "source": {{
        "document_name": "quy_che.pdf",
        "page_number": 12,
        "chunk_id": "chunk_15",
        "evidence_text": "Đoạn nội dung chứng minh",
        "category": "tot_nghiep"
      }}
    }}
  ]
}}

NỘI DUNG TRUY XUẤT TỪ KHO TRI THỨC:

{context}
""".strip()

    @staticmethod
    def _extract_json(
        response_text: str,
    ) -> dict[str, Any]:
        """
        Tách JSON object từ nội dung LLM trả về.
        """

        if not response_text:
            raise GraduationRuleExtractionError(
                "LLM không trả về nội dung."
            )

        text = response_text.strip()

        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
        )

        try:
            result = json.loads(text)

        except json.JSONDecodeError:
            # Thử lấy JSON object nếu model chèn
            # thêm nội dung trước hoặc sau JSON.
            start_index = text.find("{")
            end_index = text.rfind("}")

            if (
                start_index < 0
                or end_index < 0
                or end_index <= start_index
            ):
                raise GraduationRuleExtractionError(
                    "LLM không trả về JSON hợp lệ."
                )

            json_text = text[
                start_index:end_index + 1
            ]

            try:
                result = json.loads(
                    json_text
                )
            except json.JSONDecodeError as error:
                raise (
                    GraduationRuleExtractionError(
                        "LLM không trả về JSON "
                        "hợp lệ."
                    )
                ) from error

        if not isinstance(result, dict):
            raise GraduationRuleExtractionError(
                "Kết quả trích xuất phải là "
                "JSON object."
            )

        return result

    def _parse_rule_set(
        self,
        response_text: str,
    ) -> GraduationRuleSet:
        """
        Parse nội dung LLM thành GraduationRuleSet.
        """

        raw_rule_set = self._extract_json(
            response_text
        )

        try:
            return GraduationRuleSet.model_validate(
                raw_rule_set
            )
        except Exception as error:
            raise GraduationRuleExtractionError(
                "JSON không đúng schema "
                "GraduationRuleSet. "
                f"Chi tiết: {error}"
            ) from error

    @staticmethod
    def _validate_rule_set(
        rule_set: GraduationRuleSet,
    ) -> list[str]:
        """
        Kiểm tra tính hợp lệ nghiệp vụ của bộ luật.

        Trả về danh sách cảnh báo nếu hợp lệ.
        Raise lỗi nếu bộ luật không hợp lệ.
        """

        validation_result = (
            GraduationRuleValidator.validate(
                rule_set
            )
        )

        if not validation_result.is_valid:
            raise GraduationRuleExtractionError(
                "Bộ luật không hợp lệ: "
                + "; ".join(
                    validation_result.errors
                )
            )

        return validation_result.warnings

    def _repair_rule_set(
        self,
        *,
        original_response: str,
        validation_error: str,
    ) -> GraduationRuleSet:
        """
        Yêu cầu LLM sửa bộ luật không hợp lệ.

        Chỉ sửa tối đa một lần để tránh vòng lặp
        gọi LLM vô hạn.
        """

        repair_prompt = f"""
Bạn đã sinh một bộ luật xét tốt nghiệp dưới dạng
JSON nhưng bộ luật không vượt qua bước kiểm tra.

LỖI KIỂM TRA:

{validation_error}

JSON HIỆN TẠI:

{original_response}

Hãy sửa JSON theo các yêu cầu sau:

1. Chỉ trả về một JSON object hợp lệ.
2. Không dùng Markdown.
3. Không viết giải thích ngoài JSON.
4. Không tạo thêm quy định không có căn cứ trong
   JSON hiện tại.
5. Với operator "in" hoặc "not_in",
   accepted_values phải có ít nhất một giá trị.
6. Nếu không đủ căn cứ xác định accepted_values,
   hãy xóa luật đó khỏi danh sách rules.
7. Không tự đoán trạng thái, ngưỡng điểm hoặc
   giá trị bị loại trừ.
8. Với operator số, required_value phải là số.
9. Không để required_value và accepted_values
   mâu thuẫn với nhau.
10. Giữ nguyên nguồn và evidence_text nếu luật
    đó vẫn được giữ lại.
11. Không thay đổi những luật đang hợp lệ.
""".strip()

        repaired_text = self.generate_text(
            repair_prompt
        )

        repaired_rule_set = (
            self._parse_rule_set(
                repaired_text
            )
        )

        warnings = self._validate_rule_set(
            repaired_rule_set
        )

        repaired_rule_set.extraction_notes.append(
            "Bộ luật đã được LLM sửa tự động "
            "một lần sau khi không vượt qua "
            "validation."
        )

        repaired_rule_set.extraction_notes.extend(
            warnings
        )

        return repaired_rule_set

    def extract(
        self,
        *,
        retrieved_chunks: list[
            dict[str, Any]
        ],
        major: str | None = None,
        cohort: str | None = None,
    ) -> GraduationRuleSet:
        """
        Trích xuất và kiểm tra bộ luật tốt nghiệp.
        """

        if not retrieved_chunks:
            raise GraduationRuleExtractionError(
                "Không có đoạn tri thức để "
                "trích xuất bộ luật."
            )

        prompt = self.build_prompt(
            retrieved_chunks=retrieved_chunks,
            major=major,
            cohort=cohort,
        )

        response_text = self.generate_text(
            prompt
        )

        try:
            rule_set = self._parse_rule_set(
                response_text
            )

            warnings = self._validate_rule_set(
                rule_set
            )

            rule_set.extraction_notes.extend(
                warnings
            )

            return rule_set

        except GraduationRuleExtractionError as error:
            try:
                return self._repair_rule_set(
                    original_response=(
                        response_text
                    ),
                    validation_error=str(error),
                )

            except Exception as repair_error:
                raise GraduationRuleExtractionError(
                    "Không thể tạo bộ luật hợp lệ. "
                    f"Lỗi ban đầu: {error}. "
                    "Lỗi sau khi sửa tự động: "
                    f"{repair_error}"
                ) from repair_error