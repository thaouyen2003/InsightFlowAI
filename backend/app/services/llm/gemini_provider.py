import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.services.llm.base import BaseLLMProvider
from app.services.llm.llm_result import LLMResult


class GeminiProvider(BaseLLMProvider):
    """
    Provider gọi Google Gemini.

    Provider không xử lý nghiệp vụ dashboard.
    Nó chỉ nhận prompt, gọi Gemini và trả về kết quả
    theo định dạng LLMResult.
    """

    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        load_dotenv(
            dotenv_path=".env",
            override=True,
        )

        self.api_key = (
            api_key
            or os.getenv(
                "GEMINI_API_KEY",
                "",
            )
        ).strip()

        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                "gemini-3.5-flash",
            )
        ).strip()

        self.client: genai.Client | None = None

        if self.api_key:
            self.client = genai.Client(
                api_key=self.api_key,
            )

    @property
    def available(self) -> bool:
        """
        Kiểm tra Gemini đã sẵn sàng sử dụng hay chưa.
        """
        return bool(
            self.api_key
            and self.client is not None
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_schema: type[Any] | None = None,
    ) -> LLMResult:
        """
        Gửi prompt đến Gemini.

        Nếu có response_schema, Gemini được yêu cầu
        trả về JSON đúng schema đó.
        """

        if not self.api_key:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "Không tìm thấy GEMINI_API_KEY "
                    "trong file .env."
                ),
            )

        if self.client is None:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "Gemini client chưa được khởi tạo."
                ),
            )

        try:
            config_arguments: dict[str, Any] = {
                "temperature": 0.2,
            }

            if system_prompt:
                config_arguments[
                    "system_instruction"
                ] = system_prompt

            if response_schema is not None:
                config_arguments[
                    "response_mime_type"
                ] = "application/json"

                config_arguments[
                    "response_schema"
                ] = response_schema

            response = (
                self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        **config_arguments
                    ),
                )
            )

            if not response.text:
                return LLMResult(
                    success=False,
                    provider=self.provider_name,
                    model=self.model,
                    error=(
                        "Gemini không trả về nội dung."
                    ),
                )

            return LLMResult(
                success=True,
                content=response.text,
                provider=self.provider_name,
                model=self.model,
                metadata={
                    "structured_output": (
                        response_schema is not None
                    ),
                },
            )

        except Exception as error:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=str(error),
            )