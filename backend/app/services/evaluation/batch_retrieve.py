import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "ground_truth_candidates.json"
OUTPUT_FILE = BASE_DIR / "retrieval_results.json"

API_URL = "http://127.0.0.1:8000/knowledge/search"


def search_knowledge(question: str, category: str, top_k: int = 5):
    payload = {
        "query": question,
        "category": category,
        "top_k": top_k,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP {e.code}",
            "detail": e.read().decode("utf-8"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def main():
    if not INPUT_FILE.exists():
        print(f"Không tìm thấy file: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    output = []

    total = len(questions)

    for index, item in enumerate(questions, start=1):
        question_id = item.get("id")
        question = item["question"]
        category = item["category"]
        top_k = item.get("top_k", 5)

        print(
            f"[{index}/{total}] "
            f"Câu {question_id}: {question}"
        )

        result = search_knowledge(
            question=question,
            category=category,
            top_k=top_k,
        )

        simplified_results = []

        for rank, chunk in enumerate(
            result.get("results", []),
            start=1,
        ):
            simplified_results.append({
                "rank": rank,
                "chunk_id": chunk.get("chunk_id"),
                "source": chunk.get("source"),
                "page": chunk.get("page"),
                "distance": chunk.get("distance"),
                "content": chunk.get("content"),
            })

        output.append({
            "id": question_id,
            "question": question,
            "category": category,
            "top_k": top_k,
            "retrieved": simplified_results,
            "reference_chunk_ids": item.get(
                "reference_chunk_ids",
                [],
            ),
        })

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 60)
    print(f"DONE: {total} câu")
    print(f"Kết quả: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()