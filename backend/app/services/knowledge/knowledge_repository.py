import json
from pathlib import Path
from typing import Any

from app.services.knowledge.knowledge_models import (
    KnowledgeCollection,
)


class KnowledgeRepository:
    """
    Lưu và đọc tri thức dưới dạng JSON.

    Đây là lớp Knowledge Storage cơ bản trước khi
    tích hợp Vector Database.
    """

    def __init__(self) -> None:
        backend_dir = Path(
            __file__
        ).resolve().parents[3]

        self.storage_dir = (
            backend_dir
            / "database"
            / "knowledge"
        )

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        collection: KnowledgeCollection,
    ) -> Path:
        safe_filename = self._build_safe_filename(
            collection.dataset_name
        )

        output_path = (
            self.storage_dir
            / f"{safe_filename}.json"
        )

        payload = collection.model_dump(
            mode="json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return output_path

    def load(
        self,
        dataset_name: str,
    ) -> KnowledgeCollection | None:
        safe_filename = self._build_safe_filename(
            dataset_name
        )

        input_path = (
            self.storage_dir
            / f"{safe_filename}.json"
        )

        if not input_path.exists():
            return None

        with input_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload: dict[str, Any] = (
                json.load(file)
            )

        return KnowledgeCollection.model_validate(
            payload
        )

    def list_datasets(
        self,
    ) -> list[str]:
        return sorted(
            path.stem
            for path in self.storage_dir.glob(
                "*.json"
            )
        )

    def _build_safe_filename(
        self,
        dataset_name: str,
    ) -> str:
        file_stem = Path(
            dataset_name
        ).stem

        safe_name = "".join(
            character
            if character.isalnum()
            or character in {"-", "_"}
            else "_"
            for character in file_stem
        )

        return safe_name or "knowledge"