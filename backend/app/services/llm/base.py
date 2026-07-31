from abc import ABC, abstractmethod
from typing import Any

from app.services.llm.llm_result import LLMResult


class BaseLLMProvider(ABC):
    """
    Interface chung cho các nhà cung cấp LLM.

    Các provider chỉ chịu trách nhiệm:
    - Nhận system prompt và user prompt
    - Gọi mô hình
    - Trả về kết quả đã chuẩn hóa
    """

    provider_name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_schema: type[Any] | None = None,
    ) -> LLMResult:
        """
        Sinh nội dung từ mô hình ngôn ngữ.
        """
        raise NotImplementedError