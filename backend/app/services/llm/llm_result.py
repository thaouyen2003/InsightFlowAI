from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResult:
    """
    Kết quả chuẩn hóa trả về từ mọi LLM provider.
    """

    success: bool
    content: str | None = None
    provider: str | None = None
    model: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None