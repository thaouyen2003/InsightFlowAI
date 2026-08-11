from app.services.knowledge.knowledge_builder import (
    KnowledgeBuilder,
)
from app.services.knowledge.knowledge_repository import (
    KnowledgeRepository,
)


insights = [
    {
        "id": "insight_001",
        "type": "missing",
        "category": "data_quality",
        "title": "Thiếu dữ liệu chuyên cần",
        "description": (
            "Cột attendance có dữ liệu bị thiếu."
        ),
        "severity": "warning",
        "metric": "missing_rate",
        "value": 12.5,
        "evidence": {
            "column": "attendance",
            "missing_rate": 12.5,
        },
    }
]


recommendations = [
    {
        "id": "recommendation_001",
        "title": "Bổ sung dữ liệu chuyên cần",
        "description": (
            "Cần kiểm tra và cập nhật các bản ghi "
            "chuyên cần còn thiếu."
        ),
        "priority": "high",
        "actions": [
            "Đối chiếu dữ liệu lớp học",
            "Cập nhật bản ghi còn thiếu",
        ],
        "based_on": "insight_001",
    }
]


builder = KnowledgeBuilder()

collection = builder.build(
    dataset_name="student.csv",
    insights=insights,
    recommendations=recommendations,
)

repository = KnowledgeRepository()

output_path = repository.save(
    collection
)

loaded_collection = repository.load(
    "student.csv"
)

print(
    "OUTPUT PATH:",
    output_path,
)

print(
    collection.model_dump_json(
        indent=2,
    )
)

print(
    "LOADED:",
    loaded_collection is not None,
)