import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "retrieval_results.json"
OUTPUT_FILE = BASE_DIR / "ground_truth_50.json"


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = []

    auto_id = 1

    for item in data:
        item_id = item.get("id")

        # 10 câu cũ đang id = null
        if item_id is None:
            item_id = auto_id
            auto_id += 1

        output.append({
            "id": item_id,
            "question": item["question"],
            "category": item["category"],
            "top_k": item.get("top_k", 5),
            "reference_chunk_ids": item.get(
                "reference_chunk_ids",
                []
            )
        })

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    total = len(output)

    missing = [
        item
        for item in output
        if not item["reference_chunk_ids"]
    ]

    print("=" * 60)
    print(f"TOTAL: {total}")
    print(f"MISSING: {len(missing)}")
    print("=" * 60)

    for item in missing:
        print(
            item["id"],
            item["question"]
        )

    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()