from typing import Any

from app.services.llm.gemini_provider import (
    GeminiProvider,
)
from app.services.llm.llm_result import (
    LLMResult,
)
from app.services.llm.openrouter_provider import (
    OpenRouterProvider,
)


class LLMManager:
    """
    Quản lý nhiều LLM provider.

    Thứ tự ưu tiên:

    1. Gemini
    2. OpenRouter
    """

    def __init__(self) -> None:
        self.gemini = GeminiProvider()
        self.openrouter = OpenRouterProvider()

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_schema: type[Any] | None = None,
    ) -> LLMResult:

        providers = [
            self.gemini,
            self.openrouter,
        ]

        last_error = "Không có provider khả dụng."

        for provider in providers:

            if not provider.available:
                continue

            result = provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
            )

            if result.success:
                return result

            print(
                f"[LLMManager] "
                f"{provider.provider_name} failed:",
                result.error,
            )
            last_provider = "none"
            last_model: str | None = None

            last_error = (
                result.error
                or last_error
            )

        return LLMResult(
            success=False,
            provider=last_provider,
            model=last_model,
            error=last_error,
        )