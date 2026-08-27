import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FILE = BASE_DIR / "retrieval_results.json"

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

missing = [
    item for item in data
    if not item.get("reference_chunk_ids")
]

print("=" * 60)
print("TOTAL:", len(data))
print("MISSING:", len(missing))
print("=" * 60)

for item in missing:
    print(
        f'ID={item.get("id")} | '
        f'{item["category"]} | '
        f'{item["question"]}'
    )