import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any

from app.services.rag.vector_store import VectorStore


class CorpusStatistics:
    """
    Thống kê corpus đang được index trong ChromaDB.

    Các thống kê chính:
    - số document
    - số chunk
    - số page
    - phân bố document/chunk theo category
    - số chunk trên mỗi document
    - độ dài chunk
    - table-like chunks
    - list-like chunks
    - numeric-heavy chunks
    - course-code-heavy chunks

    Lưu ý:
    Các nhãn table-like/list-like/... là heuristic,
    không phải structural labels từ document parser.
    """

    def __init__(self) -> None:
        self.vector_store = VectorStore()

        self.evaluation_dir = (
            Path(__file__)
            .resolve()
            .parent
        )

        self.results_dir = (
            self.evaluation_dir
            / "results"
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # LOAD CORPUS
    # =========================================================

    def load_corpus(
        self,
    ) -> list[dict[str, Any]]:
        """
        Đọc toàn bộ chunks + metadata từ ChromaDB.
        """

        response = self.vector_store.collection.get(
            include=[
                "documents",
                "metadatas",
            ]
        )

        ids = response.get("ids") or []
        documents = response.get("documents") or []
        metadatas = response.get("metadatas") or []

        corpus: list[dict[str, Any]] = []

        for chunk_id, document, metadata in zip(
            ids,
            documents,
            metadatas,
            strict=False,
        ):
            content = str(
                document or ""
            ).strip()

            metadata = dict(
                metadata or {}
            )

            if not content:
                continue

            corpus.append(
                {
                    "chunk_id":
                        str(chunk_id),

                    "content":
                        content,

                    "metadata":
                        metadata,

                    "source":
                        str(
                            metadata.get(
                                "source",
                                "unknown",
                            )
                        ),

                    "path":
                        str(
                            metadata.get(
                                "path",
                                "",
                            )
                        ),

                    "category":
                        str(
                            metadata.get(
                                "category",
                                "unknown",
                            )
                        ),

                    "page":
                        metadata.get("page"),

                    "chunk_index":
                        metadata.get(
                            "chunk_index"
                        ),
                }
            )

        return corpus

    # =========================================================
    # HEURISTICS
    # =========================================================

    @staticmethod
    def is_table_like(
        content: str,
    ) -> bool:
        """
        Ước lượng chunk có đặc trưng giống bảng.

        Không khẳng định đây là bảng thực sự.

        Các dấu hiệu:
        - nhiều số / mã
        - nhiều dòng ngắn
        - các heading thường xuất hiện trong bảng CTĐT
        """

        text = content.strip()

        if not text:
            return False

        lower = text.lower()

        table_keywords = [
            "stt",
            "mã hp",
            "tên học phần",
            "số tín chỉ",
            "tổng lt",
            "th/ tn",
            "mã hp học trước",
        ]

        keyword_matches = sum(
            1
            for keyword in table_keywords
            if keyword in lower
        )

        tokens = re.findall(
            r"\S+",
            text,
        )

        if not tokens:
            return False

        numeric_tokens = sum(
            1
            for token in tokens
            if re.search(
                r"\d",
                token,
            )
        )

        numeric_ratio = (
            numeric_tokens
            / len(tokens)
        )

        # Table header mạnh.
        if keyword_matches >= 2:
            return True

        # Nhiều mã + số.
        course_codes = re.findall(
            r"\b[A-Z]{2,6}\d{2,4}\b",
            text,
        )

        if (
            len(course_codes) >= 3
            and numeric_ratio >= 0.15
        ):
            return True

        return False

    @staticmethod
    def is_list_like(
        content: str,
    ) -> bool:
        """
        Ước lượng chunk có cấu trúc danh sách.
        """

        patterns = [
            r"(?:^|\n)\s*[-–•]\s+",
            r"(?:^|\n)\s*\d+[.)]\s+",
            r"(?:^|\n)\s*[a-zA-Z][.)]\s+",
        ]

        matches = 0

        for pattern in patterns:
            matches += len(
                re.findall(
                    pattern,
                    content,
                    flags=re.MULTILINE,
                )
            )

        return matches >= 2

    @staticmethod
    def is_numeric_heavy(
        content: str,
    ) -> bool:
        """
        Chunk chứa tỷ lệ token có số tương đối cao.
        """

        tokens = re.findall(
            r"\S+",
            content,
        )

        if not tokens:
            return False

        numeric_tokens = sum(
            1
            for token in tokens
            if re.search(
                r"\d",
                token,
            )
        )

        ratio = (
            numeric_tokens
            / len(tokens)
        )

        return ratio >= 0.20

    @staticmethod
    def is_course_code_heavy(
        content: str,
    ) -> bool:
        """
        Chunk chứa nhiều mã học phần.

        Ví dụ:
        INT468
        INT469
        INT520
        """

        codes = re.findall(
            r"\b[A-Z]{2,6}\d{2,4}\b",
            content,
        )

        return len(codes) >= 3

    # =========================================================
    # COMPUTE STATISTICS
    # =========================================================

    def compute(
        self,
    ) -> dict[str, Any]:

        corpus = self.load_corpus()

        if not corpus:
            raise RuntimeError(
                "Corpus trong ChromaDB đang rỗng."
            )

        # =====================================================
        # BASIC COUNTS
        # =====================================================

        total_chunks = len(corpus)

        sources = {
            item["source"]
            for item in corpus
        }

        total_documents = len(
            sources
        )

        # Unique page được xác định bằng
        # (source, page), không chỉ page number.

        unique_pages = {
            (
                item["source"],
                item["page"],
            )
            for item in corpus
            if item["page"] is not None
        }

        total_pages = len(
            unique_pages
        )

        # =====================================================
        # CHUNK LENGTH
        # =====================================================

        char_lengths = [
            len(
                item["content"]
            )
            for item in corpus
        ]

        word_lengths = [
            len(
                re.findall(
                    r"\S+",
                    item["content"],
                )
            )
            for item in corpus
        ]

        # =====================================================
        # CHUNKS PER DOCUMENT
        # =====================================================

        chunks_per_document = Counter(
            item["source"]
            for item in corpus
        )

        chunks_per_document_values = list(
            chunks_per_document.values()
        )

        # =====================================================
        # CATEGORY DISTRIBUTION
        # =====================================================

        chunks_by_category = Counter(
            item["category"]
            for item in corpus
        )

        all_categories = sorted(
            chunks_by_category.keys()
        )
        
        documents_by_category: dict[
            str,
            set[str],
        ] = defaultdict(set)

        pages_by_category: dict[
            str,
            set[tuple[str, Any]],
        ] = defaultdict(set)

        for item in corpus:
            category = item[
                "category"
            ]

            documents_by_category[
                category
            ].add(
                item["source"]
            )

            if item["page"] is not None:
                pages_by_category[
                    category
                ].add(
                    (
                        item["source"],
                        item["page"],
                    )
                )



        structural_by_category = {}
        for category in all_categories:
            category_items = [
                item
                for item in corpus
                if item["category"] == category
            ]

            category_count = len(category_items)

            table_count = sum(
                self.is_table_like(item["content"])
                for item in category_items
            )

            list_count = sum(
                self.is_list_like(item["content"])
                for item in category_items
            )

            numeric_count = sum(
                self.is_numeric_heavy(item["content"])
                for item in category_items
            )

            course_code_count = sum(
                self.is_course_code_heavy(item["content"])
                for item in category_items
            )


            structural_by_category[category] = {
                "chunks": category_count,

                "table_like": {
                    "count": table_count,
                    "percentage": (
                        table_count / category_count * 100
                        if category_count
                        else 0.0
                    ),
                },

                "list_like": {
                    "count": list_count,
                    "percentage": (
                        list_count / category_count * 100
                        if category_count
                        else 0.0
                    ),
                },

                "numeric_heavy": {
                    "count": numeric_count,
                    "percentage": (
                        numeric_count / category_count * 100
                        if category_count
                        else 0.0
                    ),
                },

                "course_code_heavy": {
                    "count": course_code_count,
                    "percentage": (
                        course_code_count / category_count * 100
                        if category_count
                        else 0.0
                    ),
                },
            }


        # =====================================================
        # STRUCTURAL HEURISTICS
        # =====================================================

        table_like_ids = [
            item["chunk_id"]
            for item in corpus
            if self.is_table_like(
                item["content"]
            )
        ]

        list_like_ids = [
            item["chunk_id"]
            for item in corpus
            if self.is_list_like(
                item["content"]
            )
        ]

        numeric_heavy_ids = [
            item["chunk_id"]
            for item in corpus
            if self.is_numeric_heavy(
                item["content"]
            )
        ]

        course_code_heavy_ids = [
            item["chunk_id"]
            for item in corpus
            if self.is_course_code_heavy(
                item["content"]
            )
        ]

        # =====================================================
        # CATEGORY DETAILS
        # =====================================================

        category_summary: dict[
            str,
            dict[str, Any],
        ] = {}

        
        for category in all_categories:

            category_chunks = (
                chunks_by_category[
                    category
                ]
            )

            category_summary[
                category
            ] = {
                "documents":
                    len(
                        documents_by_category[
                            category
                        ]
                    ),

                "pages":
                    len(
                        pages_by_category[
                            category
                        ]
                    ),

                "chunks":
                    category_chunks,

                "chunk_percentage":
                    (
                        category_chunks
                        / total_chunks
                        * 100
                    ),
            }

        # =====================================================
        # DOCUMENT DETAILS
        # =====================================================

        document_summary = []

        for source in sorted(
            sources
        ):
            document_items = [
                item
                for item in corpus
                if item["source"] == source
            ]

            pages = {
                item["page"]
                for item in document_items
                if item["page"] is not None
            }

            categories = sorted(
                {
                    item["category"]
                    for item in document_items
                }
            )

            document_summary.append(
                {
                    "source":
                        source,

                    "categories":
                        categories,

                    "pages":
                        len(pages),

                    "chunks":
                        len(document_items),

                    "mean_chunk_chars":
                        mean(
                            len(item["content"])
                            for item
                            in document_items
                        ),
                }
            )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        result = {
            "collection":
                self.vector_store.COLLECTION_NAME,

            "total_documents":
                total_documents,

            "total_pages":
                total_pages,

            "total_chunks":
                total_chunks,

            "chunk_length_characters": {
                "mean":
                    mean(char_lengths),

                "median":
                    median(char_lengths),

                "min":
                    min(char_lengths),

                "max":
                    max(char_lengths),

                "std":
                    pstdev(char_lengths),
            },

            "chunk_length_words": {
                "mean":
                    mean(word_lengths),

                "median":
                    median(word_lengths),

                "min":
                    min(word_lengths),

                "max":
                    max(word_lengths),

                "std":
                    pstdev(word_lengths),
            },

            "chunks_per_document": {
                "mean":
                    mean(
                        chunks_per_document_values
                    ),

                "median":
                    median(
                        chunks_per_document_values
                    ),

                "min":
                    min(
                        chunks_per_document_values
                    ),

                "max":
                    max(
                        chunks_per_document_values
                    ),
            },

            "structural_heuristics": {
                "table_like": {
                    "count":
                        len(table_like_ids),

                    "percentage":
                        (
                            len(table_like_ids)
                            / total_chunks
                            * 100
                        ),

                    "chunk_ids":
                        table_like_ids,
                },

                "list_like": {
                    "count":
                        len(list_like_ids),

                    "percentage":
                        (
                            len(list_like_ids)
                            / total_chunks
                            * 100
                        ),

                    "chunk_ids":
                        list_like_ids,
                },

                "numeric_heavy": {
                    "count":
                        len(
                            numeric_heavy_ids
                        ),

                    "percentage":
                        (
                            len(numeric_heavy_ids)
                            / total_chunks
                            * 100
                        ),

                    "chunk_ids":
                        numeric_heavy_ids,
                },

                "course_code_heavy": {
                    "count":
                        len(
                            course_code_heavy_ids
                        ),

                    "percentage":
                        (
                            len(
                                course_code_heavy_ids
                            )
                            / total_chunks
                            * 100
                        ),

                    "chunk_ids":
                        course_code_heavy_ids,
                },
            },

            "category_summary":
                category_summary,

            "document_summary":
                document_summary,
            "structural_by_category":
                structural_by_category,
        }

        return result

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        result: dict[str, Any],
    ) -> Path:

        output_file = (
            self.results_dir
            / "corpus_statistics.json"
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


# =============================================================
# PRINT
# =============================================================


def print_statistics(
    result: dict[str, Any],
) -> None:

    print(
        "\n=== CORPUS STATISTICS ==="
    )

    print(
        "Collection:",
        result["collection"],
    )

    print(
        "Documents:",
        result["total_documents"],
    )

    print(
        "Pages:",
        result["total_pages"],
    )

    print(
        "Chunks:",
        result["total_chunks"],
    )

    print(
        "\n=== CHUNK LENGTH ==="
    )

    chars = result[
        "chunk_length_characters"
    ]

    print(
        "Characters mean:",
        f'{chars["mean"]:.2f}',
    )

    print(
        "Characters median:",
        f'{chars["median"]:.2f}',
    )

    print(
        "Characters range:",
        f'{chars["min"]} - {chars["max"]}',
    )

    words = result[
        "chunk_length_words"
    ]

    print(
        "Words mean:",
        f'{words["mean"]:.2f}',
    )

    print(
        "Words median:",
        f'{words["median"]:.2f}',
    )

    print(
        "Words range:",
        f'{words["min"]} - {words["max"]}',
    )

    print(
        "\n=== CHUNKS PER DOCUMENT ==="
    )

    cpd = result[
        "chunks_per_document"
    ]

    print(
        "Mean:",
        f'{cpd["mean"]:.2f}',
    )

    print(
        "Median:",
        f'{cpd["median"]:.2f}',
    )

    print(
        "Range:",
        f'{cpd["min"]} - {cpd["max"]}',
    )

    print(
        "\n=== CATEGORY DISTRIBUTION ==="
    )

    for category, stats in (
        result[
            "category_summary"
        ].items()
    ):
        print(
            f"\n[{category}]"
        )

        print(
            "Documents:",
            stats["documents"],
        )

        print(
            "Pages:",
            stats["pages"],
        )

        print(
            "Chunks:",
            stats["chunks"],
        )

        print(
            "Chunk percentage:",
            f'{stats["chunk_percentage"]:.2f}%',
        )

    print(
        "\n=== STRUCTURAL HEURISTICS ==="
    )

    for name, stats in (
        result[
            "structural_heuristics"
        ].items()
    ):
        print(
            f'{name}: '
            f'{stats["count"]} '
            f'({stats["percentage"]:.2f}%)'
        )

    print(
    "\n=== STRUCTURAL CHARACTERISTICS BY CATEGORY ==="
    )

    for category, stats in (
        result["structural_by_category"].items()
    ):
        print(f"\n[{category}]")
        print("Chunks:", stats["chunks"])

        for feature in [
            "table_like",
            "list_like",
            "numeric_heavy",
            "course_code_heavy",
        ]:
            feature_stats = stats[feature]

            print(
                f'{feature}: '
                f'{feature_stats["count"]} '
                f'({feature_stats["percentage"]:.2f}%)'
            )

# =============================================================
# MAIN
# =============================================================


if __name__ == "__main__":

    service = CorpusStatistics()

    result = service.compute()

    print_statistics(
        result
    )

    output_file = service.save(
        result
    )

    print(
        "\nSaved:",
        output_file,
    )