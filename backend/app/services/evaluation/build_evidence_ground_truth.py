import json
from pathlib import Path
from typing import Any

from app.services.rag.vector_store import VectorStore


class EvidenceGroundTruthBuilder:
    def __init__(self) -> None:
        self.vector_store = VectorStore()

        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        self.input_file = (
            self.evaluation_dir
            / "ground_truth_50.json"
        )

        self.output_file = (
            self.evaluation_dir
            / "ground_truth_evidence.json"
        )

    def load_test_cases(
        self,
    ) -> list[dict[str, Any]]:
        data = json.loads(
            self.input_file.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            return data.get(
                "test_cases",
                [],
            )

        if isinstance(data, list):
            return data

        raise ValueError(
            "Ground truth format không hợp lệ."
        )

    def load_chunks(
        self,
    ) -> dict[str, dict[str, Any]]:
        response = (
            self.vector_store
            .collection
            .get(
                include=[
                    "documents",
                    "metadatas",
                ]
            )
        )

        ids = response.get("ids") or []
        documents = response.get(
            "documents"
        ) or []
        metadatas = response.get(
            "metadatas"
        ) or []

        chunks: dict[
            str,
            dict[str, Any],
        ] = {}

        for (
            chunk_id,
            content,
            metadata,
        ) in zip(
            ids,
            documents,
            metadatas,
            strict=False,
        ):
            chunks[str(chunk_id)] = {
                "content":
                    str(content or "").strip(),

                "metadata":
                    dict(metadata or {}),
            }

        return chunks

    def build(
        self,
    ) -> list[dict[str, Any]]:
        test_cases = (
            self.load_test_cases()
        )

        chunks = (
            self.load_chunks()
        )

        output = []

        missing = []

        for case in test_cases:
            references = []

            for chunk_id in case.get(
                "reference_chunk_ids",
                [],
            ):
                chunk = chunks.get(
                    chunk_id
                )

                if chunk is None:
                    missing.append(
                        {
                            "question_id":
                                case.get("id"),

                            "chunk_id":
                                chunk_id,
                        }
                    )

                    continue

                metadata = chunk[
                    "metadata"
                ]

                references.append(
                    {
                        "chunk_id":
                            chunk_id,

                        "source":
                            metadata.get(
                                "source"
                            ),

                        "page":
                            metadata.get(
                                "page"
                            ),

                        "category":
                            metadata.get(
                                "category"
                            ),

                        "content":
                            chunk[
                                "content"
                            ],
                    }
                )

            output.append(
                {
                    "id":
                        case.get("id"),

                    "question":
                        case.get(
                            "question"
                        ),

                    "category":
                        case.get(
                            "category"
                        ),

                    "top_k":
                        case.get(
                            "top_k",
                            5,
                        ),

                    "reference_chunk_ids":
                        case.get(
                            "reference_chunk_ids",
                            [],
                        ),

                    "reference_evidence":
                        references,
                }
            )

        if missing:
            print(
                "\n=== MISSING REFERENCES ==="
            )

            for item in missing:
                print(
                    item
                )

        return output

    def save(
        self,
        cases: list[dict[str, Any]],
    ) -> None:
        self.output_file.write_text(
            json.dumps(
                cases,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "\nSaved:",
            self.output_file,
        )


if __name__ == "__main__":
    builder = (
        EvidenceGroundTruthBuilder()
    )

    cases = builder.build()

    builder.save(
        cases
    )

    print(
        "Cases:",
        len(cases),
    )

    print(
        "Evidence records:",
        sum(
            len(
                case[
                    "reference_evidence"
                ]
            )
            for case in cases
        ),
    )