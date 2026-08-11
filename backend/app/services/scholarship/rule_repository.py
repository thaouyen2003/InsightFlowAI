from __future__ import annotations

import json
from pathlib import Path

from app.services.scholarship.rules import (
    ScholarshipRuleSet,
)


class ScholarshipRuleRepository:
    """
    Lưu và đọc bộ luật học bổng đã được
    trích xuất từ Knowledge Base.
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
    ) -> None:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        self.storage_dir = (
            Path(storage_dir)
            if storage_dir
            else (
                backend_dir
                / "database"
                / "scholarship_rules"
            )
        )

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _safe_filename(
        rule_set_code: str,
    ) -> str:
        return (
            rule_set_code
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

    def save(
        self,
        rule_set: ScholarshipRuleSet,
    ) -> Path:
        filename = (
            self._safe_filename(
                rule_set.rule_set_code
            )
            + ".json"
        )

        output_path = (
            self.storage_dir
            / filename
        )

        output_path.write_text(
            rule_set.model_dump_json(
                indent=2
            ),
            encoding="utf-8",
        )

        return output_path

    def load(
        self,
        rule_set_code: str,
    ) -> ScholarshipRuleSet:
        filename = (
            self._safe_filename(
                rule_set_code
            )
            + ".json"
        )

        input_path = (
            self.storage_dir
            / filename
        )

        if not input_path.exists():
            raise FileNotFoundError(
                "Không tìm thấy bộ luật học bổng: "
                f"{rule_set_code}"
            )

        raw_data = json.loads(
            input_path.read_text(
                encoding="utf-8"
            )
        )

        return (
            ScholarshipRuleSet
            .model_validate(raw_data)
        )