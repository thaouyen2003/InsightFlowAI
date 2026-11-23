import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.services.rag.vector_store import (
    VectorStore,
)


class FrozenCorpusBuilder:
    """
    Tái dựng nội dung từng page từ collection
    vhu_knowledge hiện tại.

    Collection gốc được xem là source of truth
    cho chunking ablation.
    """

    def __init__(self) -> None:
        self.store = VectorStore(
            collection_name="vhu_knowledge"
        )

        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        self.output_file = (
            self.evaluation_dir
            / "frozen_corpus_pages.json"
        )

    # =========================================================
    # WORD OVERLAP
    # =========================================================

    @staticmethod
    def merge_chunks(
        chunks: list[str],
    ) -> str:
        """
        Ghép các chunk của cùng một page bằng cách
        loại bỏ phần word-overlap giữa chunk liên tiếp.
        """

        if not chunks:
            return ""

        merged_words = (
            chunks[0]
            .strip()
            .split()
        )

        for chunk in chunks[1:]:
            next_words = (
                chunk
                .strip()
                .split()
            )

            if not next_words:
                continue

            max_overlap = min(
                len(merged_words),
                len(next_words),
            )

            overlap = 0

            for size in range(
                max_overlap,
                0,
                -1,
            ):
                if (
                    merged_words[-size:]
                    == next_words[:size]
                ):
                    overlap = size
                    break

            merged_words.extend(
                next_words[
                    overlap:
                ]
            )

        return " ".join(
            merged_words
        ).strip()

    # =========================================================
    # BUILD
    # =========================================================

    def build(
        self,
    ) -> list[dict[str, Any]]:

        response = (
            self.store.collection.get(
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

        pages: dict[
            tuple[str, int],
            list[dict[str, Any]],
        ] = defaultdict(list)

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

            source = metadata.get(
                "source"
            )

            page = metadata.get(
                "page"
            )

            if (
                source is None
                or page is None
            ):
                continue

            pages[
                (
                    str(source),
                    int(page),
                )
            ].append(
                {
                    "chunk_id":
                        str(chunk_id),

                    "chunk_index":
                        int(
                            metadata.get(
                                "chunk_index",
                                0,
                            )
                        ),

                    "content":
                        str(
                            content or ""
                        ).strip(),

                    "category":
                        metadata.get(
                            "category"
                        ),

                    "path":
                        metadata.get(
                            "path"
                        ),
                }
            )

        frozen_pages = []

        for (
            source,
            page,
        ), chunks in sorted(
            pages.items(),
            key=lambda value: (
                value[0][0],
                value[0][1],
            ),
        ):
            chunks.sort(
                key=lambda item:
                    item["chunk_index"]
            )

            page_content = (
                self.merge_chunks(
                    [
                        item["content"]
                        for item in chunks
                    ]
                )
            )

            frozen_pages.append(
                {
                    "source":
                        source,

                    "page":
                        page,

                    "category":
                        chunks[0][
                            "category"
                        ],

                    "path":
                        chunks[0][
                            "path"
                        ],

                    "content":
                        page_content,

                    "original_chunk_count":
                        len(chunks),

                    "original_chunk_ids":
                        [
                            item[
                                "chunk_id"
                            ]
                            for item
                            in chunks
                        ],
                }
            )

        return frozen_pages

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        pages: list[dict[str, Any]],
    ) -> None:

        self.output_file.write_text(
            json.dumps(
                pages,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "Saved:",
            self.output_file,
        )


if __name__ == "__main__":
    builder = FrozenCorpusBuilder()

    pages = builder.build()

    builder.save(
        pages
    )

    print(
        "Frozen pages:",
        len(pages),
    )

    print(
        "Original chunks:",
        sum(
            page[
                "original_chunk_count"
            ]
            for page in pages
        ),
    )