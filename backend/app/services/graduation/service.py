from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.services.graduation.column_normalizer import (
    GraduationColumnNormalizer,
)
from app.services.graduation.data_validator import (
    GraduationDataValidator,
)
from app.services.graduation.evaluator import (
    GraduationEvaluator,
)
from app.services.graduation.models import (
    GraduationEvaluationResponse,
)
from app.services.graduation.rule_repository import (
    GraduationRuleRepository,
)
from app.services.graduation.rule_validator import (
    GraduationRuleValidator,
)
from app.services.graduation.summary_builder import (
    GraduationSummaryBuilder,
)


class GraduationEvaluationService:
    """
    Điều phối toàn bộ quy trình đánh giá
    điều kiện tốt nghiệp.
    """

    def __init__(
        self,
        rule_repository: (
            GraduationRuleRepository | None
        ) = None,
    ) -> None:
        self.rule_repository = (
            rule_repository
            or GraduationRuleRepository()
        )

    @staticmethod
    def _build_sources(
        rule_set: Any,
    ) -> list[dict[str, Any]]:
        """
        Tổng hợp nguồn tri thức từ các luật.
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
                    "category": (
                        source.category
                    ),
                }
            )

        return sources

    def evaluate(
        self,
        *,
        df: pd.DataFrame,
        dataset_name: str,
        rule_set_code: str,
    ) -> GraduationEvaluationResponse:
        """
        Đánh giá toàn bộ dữ liệu sinh viên.
        """

        normalized_result = (
            GraduationColumnNormalizer.normalize(
                df,
                return_report=True,
            )
        )

        normalized_df, normalization_report = (
            normalized_result
        )

        validation_result = (
            GraduationDataValidator.validate(
                normalized_df
            )
        )
        rule_set = self.rule_repository.load(
            rule_set_code
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
                "Dữ liệu xét tốt nghiệp "
                "không hợp lệ. "
                + " ".join(error_messages)
            )

       

        rule_validation = (
            GraduationRuleValidator.validate(
                rule_set
            )
        )

        if not rule_validation.is_valid:
            raise ValueError(
                "Bộ luật xét tốt nghiệp "
                "không hợp lệ: "
                + "; ".join(
                    rule_validation.errors
                )
            )

        student_results = (
            GraduationEvaluator
            .evaluate_dataframe(
                normalized_df,
                rule_set=rule_set,
            )
        )

        summary = (
            GraduationSummaryBuilder.build(
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

        return GraduationEvaluationResponse(
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
    ) -> GraduationEvaluationResponse:
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