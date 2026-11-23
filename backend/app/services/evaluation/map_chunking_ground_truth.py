import json
import re
from pathlib import Path
from typing import Any

from app.services.rag.vector_store import (
    VectorStore,
)


CONFIGS = {
    "chunk_400_75":
        "vhu_knowledge_chunk_400_75",

    "chunk_800_150":
        "vhu_knowledge_chunk_800_150",

    "chunk_1200_200":
        "vhu_knowledge_chunk_1200_200",
}


class ChunkingGroundTruthMapper:
    """
    Map evidence ground truth hiện tại sang
    candidate chunks của các chunking configurations.

    Mapping dựa trên:
    - source
    - page
    - lexical content overlap

    Script chỉ sinh candidates.
    Không tự động coi candidate cao nhất
    là ground truth cuối cùng.
    """

    def __init__(
        self,
    ) -> None:
        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        self.input_file = (
            self.evaluation_dir
            / "ground_truth_evidence.json"
        )

        self.output_dir = (
            self.evaluation_dir
            / "chunking_ground_truth_candidates"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # TOKENIZE
    # =========================================================

    @staticmethod
    def tokenize(
        text: str,
    ) -> set[str]:
        """
        Tokenization đơn giản phục vụ overlap mapping.
        """

        return {
            token.lower()
            for token in re.findall(
                r"\b\w+\b",
                text,
                flags=re.UNICODE,
            )
            if len(token) > 1
        }

    # =========================================================
    # OVERLAP SCORE
    # =========================================================

    def overlap_score(
        self,
        evidence: str,
        candidate: str,
    ) -> float:
        """
        Recall-oriented lexical overlap:

        |evidence_tokens ∩ candidate_tokens|
        ------------------------------------
               |evidence_tokens|
        """

        evidence_tokens = (
            self.tokenize(
                evidence
            )
        )

        candidate_tokens = (
            self.tokenize(
                candidate
            )
        )

        if not evidence_tokens:
            return 0.0

        overlap = (
            evidence_tokens
            & candidate_tokens
        )

        return (
            len(overlap)
            / len(evidence_tokens)
        )

    # =========================================================
    # LOAD GROUND TRUTH
    # =========================================================

    def load_ground_truth(
        self,
    ) -> list[dict[str, Any]]:

        if not self.input_file.exists():
            raise FileNotFoundError(
                "Không tìm thấy: "
                f"{self.input_file}"
            )

        data = json.loads(
            self.input_file.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            list,
        ):
            raise ValueError(
                "ground_truth_evidence.json "
                "phải là danh sách."
            )

        return data

    # =========================================================
    # LOAD COLLECTION
    # =========================================================

    @staticmethod
    def load_collection(
        collection_name: str,
    ) -> list[dict[str, Any]]:

        store = VectorStore(
            collection_name=
                collection_name
        )

        response = (
            store.collection.get(
                include=[
                    "documents",
                    "metadatas",
                ]
            )
        )

        ids = (
            response.get("ids")
            or []
        )

        documents = (
            response.get("documents")
            or []
        )

        metadatas = (
            response.get("metadatas")
            or []
        )

        chunks = []

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
            metadata = dict(
                metadata or {}
            )

            chunks.append(
                {
                    "chunk_id":
                        str(chunk_id),

                    "content":
                        str(
                            content or ""
                        ).strip(),

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
                }
            )

        return chunks

    # =========================================================
    # MAP ONE CONFIG
    # =========================================================

    def map_config(
        self,
        config_name: str,
        collection_name: str,
        top_n: int = 5,
    ) -> dict[str, Any]:

        ground_truth = (
            self.load_ground_truth()
        )

        chunks = (
            self.load_collection(
                collection_name
            )
        )

        print(
            "\n========================================"
        )

        print(
            "Mapping:",
            config_name
        )

        print(
            "Collection:",
            collection_name
        )

        print(
            "Chunks:",
            len(chunks)
        )

        print(
            "========================================"
        )

        # Incomplete collection: vẫn cho map,
        # nhưng đánh dấu rõ để không dùng evaluation.
        collection_complete = (
            len(chunks) > 0
        )

        results = []

        for case in ground_truth:
            mapped_references = []

            for evidence in (
                case.get(
                    "reference_evidence",
                    []
                )
            ):
                source = evidence.get(
                    "source"
                )

                page = evidence.get(
                    "page"
                )

                evidence_content = str(
                    evidence.get(
                        "content",
                        ""
                    )
                ).strip()

                page_candidates = [
                    chunk
                    for chunk in chunks
                    if (
                        chunk["source"]
                        == source
                        and chunk["page"]
                        == page
                    )
                ]

                scored_candidates = []

                for candidate in (
                    page_candidates
                ):
                    score = (
                        self.overlap_score(
                            evidence=
                                evidence_content,

                            candidate=
                                candidate[
                                    "content"
                                ],
                        )
                    )

                    scored_candidates.append(
                        {
                            "chunk_id":
                                candidate[
                                    "chunk_id"
                                ],

                            "source":
                                candidate[
                                    "source"
                                ],

                            "page":
                                candidate[
                                    "page"
                                ],

                            "overlap_score":
                                score,

                            "content_preview":
                                candidate[
                                    "content"
                                ][:400],
                        }
                    )

                scored_candidates.sort(
                    key=lambda item:
                        item[
                            "overlap_score"
                        ],
                    reverse=True,
                )

                mapped_references.append(
                    {
                        "original_chunk_id":
                            evidence.get(
                                "chunk_id"
                            ),

                        "source":
                            source,

                        "page":
                            page,

                        "evidence_preview":
                            evidence_content[
                                :400
                            ],

                        "candidate_count":
                            len(
                                page_candidates
                            ),

                        "candidates":
                            scored_candidates[
                                :top_n
                            ],
                    }
                )

            results.append(
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

                    "mapped_references":
                        mapped_references,
                }
            )

        return {
            "config":
                config_name,

            "collection_name":
                collection_name,

            "collection_chunks":
                len(chunks),

            "collection_non_empty":
                collection_complete,

            "cases":
                results,
        }

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        config_name: str,
        result: dict[str, Any],
    ) -> Path:

        output_file = (
            self.output_dir
            / f"{config_name}_candidates.json"
        )

        output_file.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return output_file

    # =========================================================
    # RUN
    # =========================================================

    def run(
        self,
    ) -> None:

        for (
            config_name,
            collection_name,
        ) in CONFIGS.items():

            result = (
                self.map_config(
                    config_name=
                        config_name,

                    collection_name=
                        collection_name,

                    top_n=5,
                )
            )

            output_file = (
                self.save(
                    config_name=
                        config_name,

                    result=result,
                )
            )

            print(
                "Saved:",
                output_file,
            )


if __name__ == "__main__":
    mapper = (
        ChunkingGroundTruthMapper()
    )

    mapper.run()