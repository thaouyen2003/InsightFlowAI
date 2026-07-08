from dataclasses import dataclass, field, asdict
from typing import Any

# Thông tin của MỘT CỘT trong dataset

@dataclass
class ColumnProfile:
    """
    Lưu toàn bộ thông tin phân tích của một cột.
    """
    name: str
    dtype: str
    semantic_type: str
    missing: int
    unique: int

    # Một vài giá trị mẫu
    sample: list[Any] = field(default_factory=list)

    # Thống kê (min, max, mean...)
    statistics: dict[str, Any] = field(default_factory=dict)

    # Có phải khóa chính hay không
    is_primary_key: bool = False

    # Có khả năng là khóa ngoại
    is_foreign_key: bool = False

    def to_dict(self):
        """
        Chuyển object thành dict để trả về API.
        """
        return asdict(self)


# Thông tin tổng quan của dataset

@dataclass
class DatasetSummary:
    """
    Thông tin tổng quan sau khi phân tích toàn bộ dataset.
    """

    rows: int

    columns: int

    numeric_columns: int

    categorical_columns: int

    datetime_columns: int

    missing_cells: int

    def to_dict(self):
        return asdict(self)


# Kết quả cuối cùng của Schema Analyzer

@dataclass
class SchemaAnalysisResult:
    """
    Kết quả trả về cho Frontend.
    """

    summary: DatasetSummary

    schema: list[ColumnProfile]

    def to_dict(self):

        return {

            "summary": self.summary.to_dict(),

            "schema": [

                column.to_dict()

                for column in self.schema
            ]
        }