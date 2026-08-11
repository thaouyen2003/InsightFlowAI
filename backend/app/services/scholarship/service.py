from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.scholarship.column_normalizer import (
    ScholarshipColumnNormalizer,
)
from app.services.scholarship.data_validator import (
    ScholarshipDataValidator,
)
from app.services.scholarship.evaluator import (
    ScholarshipEvaluator,
)
from app.services.scholarship.models import (
    ScholarshipEvaluationResponse,
)
from app.services.scholarship.rule_repository import (
    ScholarshipRuleRepository,
)
from app.services.scholarship.rule_validator import (
    ScholarshipRuleValidator,
)
from app.services.scholarship.summary_builder import (
    ScholarshipSummaryBuilder,
)


class ScholarshipEvaluationService:
    """
    Điều phối toàn bộ quy trình đánh giá
    điều kiện học bổng.
    """

    def __init__(
        self,
        rule_repository: (
            ScholarshipRuleRepository | None
        ) = None,
    ) -> None:
        self.rule_repository = (
            rule_repository
            or ScholarshipRuleRepository()
        )

    @staticmethod
    def _build_sources(
        rule_set: Any,
    ) -> list[dict[str, Any]]:
        """
        Tổng hợp nguồn tri thức từ các luật,
        loại bỏ nguồn bị trùng.
        """

        sources: list[dict[str, Any]] = []

        seen_sources: set[
            tuple[str, int | None, str | None]
        ] = set()

        for rule in rule_set.rules:
            source = rule.source

            source_key = (
                source.document_name,
                source.page_number,
                source.chunk_id,
            )

            if source_key in seen_sources:
                continue

            seen_sources.add(source_key)

            sources.append(
                {
                    "document_name": (
                        source.document_name
                    ),
                    "page_number": (
                        source.page_number
                    ),
                    "chunk_id": source.chunk_id,
                    "evidence_text": (
                        source.evidence_text
                    ),
                    "category": source.category,
                }
            )

        return sources

    @staticmethod
    def _normalize_tuition_status(
        value: Any,
    ) -> Any:
        """
        Chuẩn hóa trạng thái học phí.

        Quy ước phổ biến:
        - 0, không nợ, đã thanh toán
          -> Hoàn thành
        - 1, còn nợ, chưa thanh toán
          -> Chưa hoàn thành
        """

        normalized_value = (
            ScholarshipEvaluator
            .normalize_status_value(value)
        )

        completed_values = {
            "0",
            "khong",
            "khong no",
            "khong con no",
            "da thanh toan",
            "hoan thanh",
            "completed",
            "paid",
            "no debt",
        }

        incomplete_values = {
            "1",
            "co",
            "con no",
            "no hoc phi",
            "chua thanh toan",
            "chua hoan thanh",
            "unpaid",
            "debt",
        }

        if normalized_value in completed_values:
            return "Hoàn thành"

        if normalized_value in incomplete_values:
            return "Chưa hoàn thành"

        return value

    @staticmethod
    def _normalize_discipline_status(
        value: Any,
    ) -> Any:
        """
        Chuẩn hóa tình trạng kỷ luật.

        Quy ước phổ biến:
        - 0, không, không kỷ luật
          -> Không kỷ luật
        - 1, có, bị kỷ luật
          -> Có kỷ luật
        """

        normalized_value = (
            ScholarshipEvaluator
            .normalize_status_value(value)
        )

        clear_values = {
            "0",
            "khong",
            "khong ky luat",
            "khong bi ky luat",
            "none",
            "no",
            "false",
        }

        disciplinary_values = {
            "1",
            "co",
            "co ky luat",
            "bi ky luat",
            "canh cao",
            "dinh chi hoc tap",
            "yes",
            "true",
        }

        if normalized_value in clear_values:
            return "Không kỷ luật"

        if normalized_value in disciplinary_values:
            return "Có kỷ luật"

        return value

    @staticmethod
    def _normalize_registration_status(
        value: Any,
    ) -> Any:
        """
        Chuẩn hóa trạng thái đăng ký học bổng.
        """

        normalized_value = (
            ScholarshipEvaluator
            .normalize_status_value(value)
        )

        on_time_values = {
            "1",
            "co",
            "dung han",
            "dang ky dung han",
            "nop dung han",
            "da dang ky",
            "on time",
            "true",
            "yes",
        }

        late_values = {
            "0",
            "khong",
            "tre han",
            "qua han",
            "chua dang ky",
            "nop tre",
            "late",
            "false",
            "no",
        }

        if normalized_value in on_time_values:
            return "Đúng hạn"

        if normalized_value in late_values:
            return "Không đúng hạn"

        return value

    @staticmethod
    def _normalize_financial_difficulty(
        value: Any,
    ) -> Any:
        """
        Chuẩn hóa thông tin hoàn cảnh khó khăn.

        Trường này chủ yếu dùng cho các loại
        học bổng hỗ trợ hoặc ưu tiên.
        """

        normalized_value = (
            ScholarshipEvaluator
            .normalize_status_value(value)
        )

        difficult_values = {
            "1",
            "co",
            "kho khan",
            "hoan canh kho khan",
            "thuoc dien kho khan",
            "yes",
            "true",
        }

        normal_values = {
            "0",
            "khong",
            "binh thuong",
            "khong kho khan",
            "no",
            "false",
        }

        if normalized_value in difficult_values:
            return "Có"

        if normalized_value in normal_values:
            return "Không"

        return value

    def evaluate(
        self,
        *,
        df: pd.DataFrame,
        dataset_name: str,
        rule_set_code: str,
    ) -> ScholarshipEvaluationResponse:
        """
        Đánh giá toàn bộ dữ liệu sinh viên
        bằng bộ luật học bổng đã lưu.
        """

        normalized_result = (
            ScholarshipColumnNormalizer.normalize(
                df,
                return_report=True,
            )
        )

        normalized_df, normalization_report = (
            normalized_result
        )

        normalized_df = normalized_df.copy()

        if (
            "tuition_status"
            in normalized_df.columns
        ):
            normalized_df[
                "tuition_status"
            ] = normalized_df[
                "tuition_status"
            ].map(
                self._normalize_tuition_status
            )

        if (
            "discipline_status"
            in normalized_df.columns
        ):
            normalized_df[
                "discipline_status"
            ] = normalized_df[
                "discipline_status"
            ].map(
                self._normalize_discipline_status
            )

        if (
            "registered_on_time"
            in normalized_df.columns
        ):
            normalized_df[
                "registered_on_time"
            ] = normalized_df[
                "registered_on_time"
            ].map(
                self._normalize_registration_status
            )

        if (
            "financial_difficulty"
            in normalized_df.columns
        ):
            normalized_df[
                "financial_difficulty"
            ] = normalized_df[
                "financial_difficulty"
            ].map(
                self._normalize_financial_difficulty
            )

        rule_set = self.rule_repository.load(
            rule_set_code
        )

        required_rule_fields = [
            rule.field_name
            for rule in rule_set.rules
            if rule.is_required
        ]

        validation_result = (
            ScholarshipDataValidator.validate(
                normalized_df,
                required_rule_fields=(
                    required_rule_fields
                ),
            )
        )

        if not validation_result.is_valid:
            error_messages: list[str] = []

            if (
                validation_result
                .missing_required_columns
            ):
                error_messages.append(
                    "Thiếu cột bắt buộc: "
                    + ", ".join(
                        validation_result
                        .missing_required_columns
                    )
                )

            if (
                validation_result
                .duplicated_student_ids
            ):
                error_messages.append(
                    "Mã sinh viên bị trùng: "
                    + ", ".join(
                        validation_result
                        .duplicated_student_ids
                    )
                )

            if (
                validation_result
                .empty_student_ids
                > 0
            ):
                error_messages.append(
                    "Có "
                    f"{validation_result.empty_student_ids} "
                    "dòng không có mã sinh viên."
                )

            raise ValueError(
                "Dữ liệu xét học bổng "
                "không hợp lệ. "
                + " ".join(error_messages)
            )

        rule_validation = (
            ScholarshipRuleValidator.validate(
                rule_set
            )
        )

        if not rule_validation.is_valid:
            raise ValueError(
                "Bộ luật xét học bổng "
                "không hợp lệ: "
                + "; ".join(
                    rule_validation.errors
                )
            )

        student_results = (
            ScholarshipEvaluator
            .evaluate_dataframe(
                normalized_df,
                rule_set=rule_set,
            )
        )

        summary = (
            ScholarshipSummaryBuilder.build(
                student_results
            )
        )

        warnings: list[str] = []

        warnings.extend(
            validation_result.warnings
        )

        warnings.extend(
            rule_validation.warnings
        )

        if (
            normalization_report
            .unrecognized_columns
        ):
            warnings.append(
                "Các cột chưa được nhận diện: "
                + ", ".join(
                    normalization_report
                    .unrecognized_columns
                )
            )

        sources = self._build_sources(
            rule_set
        )

        return ScholarshipEvaluationResponse(
            success=True,
            dataset_name=dataset_name,
            rule_set_code=(
                rule_set.rule_set_code
            ),
            rule_set_name=(
                rule_set.rule_set_name
            ),
            rule_set_version=(
                rule_set.version
            ),
            summary=summary,
            students=student_results,
            sources=sources,
            warnings=warnings,
            metadata={
                "major": rule_set.major,
                "cohort": rule_set.cohort,
                "program": rule_set.program,
                "effective_date": (
                    rule_set.effective_date
                ),
                "scholarship_type": (
                    rule_set.scholarship_type
                ),
                "generated_by": (
                    rule_set.generated_by
                ),
                "recognized_columns": (
                    normalization_report
                    .renamed_columns
                ),
                "unrecognized_columns": (
                    normalization_report
                    .unrecognized_columns
                ),
                "source_document_count": len(
                    rule_set.source_documents
                ),
                "rule_count": len(
                    rule_set.rules
                ),
            },
        )

    def evaluate_file(
        self,
        *,
        file_path: str | Path,
        rule_set_code: str,
    ) -> ScholarshipEvaluationResponse:
        """
        Đọc CSV, Excel hoặc JSON và đánh giá.
        """

        input_path = Path(file_path)

        if not input_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy file: {input_path}"
            )

        suffix = input_path.suffix.lower()

        if suffix == ".csv":
            df = pd.read_csv(input_path)

        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(input_path)

        elif suffix == ".json":
            df = pd.read_json(input_path)

        else:
            raise ValueError(
                "Chỉ hỗ trợ CSV, XLSX, XLS "
                "và JSON."
            )

        return self.evaluate(
            df=df,
            dataset_name=input_path.name,
            rule_set_code=rule_set_code,
        )