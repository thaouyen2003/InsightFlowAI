from app.services.schema.models import (
    ColumnProfile,
    DatasetSummary,
    SchemaAnalysisResult
)

column = ColumnProfile(
    name="customer_id",
    dtype="object",
    semantic_type="identifier",
    missing=0,
    unique=100
)

summary = DatasetSummary(
    rows=100,
    columns=5,
    numeric_columns=1,
    categorical_columns=4,
    datetime_columns=0,
    missing_cells=0
)

result = SchemaAnalysisResult(
    summary=summary,
    schema=[column]
)

print(result.to_dict())