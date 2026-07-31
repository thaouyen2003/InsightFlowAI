import os
from typing import Any

import httpx
from dotenv import load_dotenv

from app.services.llm.base import BaseLLMProvider
from app.services.llm.llm_result import LLMResult


class OpenRouterProvider(BaseLLMProvider):
    """
    Gọi Gemini thông qua OpenRouter.

    Provider này được dùng khi Gemini API trực tiếp
    không khả dụng, hết quota hoặc gặp lỗi tạm thời.
    """

    provider_name = "openrouter"

    API_URL = (
        "https://openrouter.ai/api/v1/chat/completions"
    )

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
                "OPENROUTER_API_KEY",
                "",
            )
        ).strip()

        self.model = (
            model
            or os.getenv(
                "OPENROUTER_MODEL",
                "google/gemini-3.5-flash",
            )
        ).strip()

        # self.timeout_seconds = self._read_timeout()
        self.timeout_seconds = min(
            self._read_timeout(),
            45,
        )
        self.max_tokens = self._read_max_tokens()

    @property
    def available(self) -> bool:
        """
        OpenRouter sẵn sàng khi có API key và model.
        """
        return bool(
            self.api_key
            and self.model
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_schema: type[Any] | None = None,
    ) -> LLMResult:
        """
        Gửi prompt đến OpenRouter.

        Nếu có Pydantic response_schema, yêu cầu model
        trả về JSON đúng schema.
        """

        if not self.api_key:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "Không tìm thấy OPENROUTER_API_KEY "
                    "trong file .env."
                ),
            )

        if not self.model:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "OPENROUTER_MODEL chưa được cấu hình."
                ),
            )

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        request_payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
        }
        if self.model == "openrouter/free":
            request_payload["reasoning"] = {
                "effort": "low",
            }

        if response_schema is not None:
            request_payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "strict": True,
                    "schema": (
                        response_schema.model_json_schema()
                    ),
                },
            }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": "application/json",
            "HTTP-Referer": (
                "https://github.com/"
                "thaouyen2003/InsightFlowAI"
            ),
            "X-Title": "InsightFlowAI",
        }

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
            ) as client:
                response = client.post(
                    self.API_URL,
                    headers=headers,
                    json=request_payload,
                )

            if response.status_code >= 400:
                return LLMResult(
                    success=False,
                    provider=self.provider_name,
                    model=self.model,
                    error=(
                        f"OpenRouter HTTP "
                        f"{response.status_code}: "
                        f"{response.text}"
                    ),
                    metadata={
                        "status_code": (
                            response.status_code
                        ),
                    },
                )

            response_data = response.json()

            choices = response_data.get(
                "choices",
                [],
            )

            if not choices:
                return LLMResult(
                    success=False,
                    provider=self.provider_name,
                    model=self.model,
                    error=(
                        "OpenRouter không trả về choices."
                    ),
                )

            first_choice = choices[0]

            message = first_choice.get(
                "message",
                {},
            )

            finish_reason = first_choice.get(
                "finish_reason"
            )

            raw_content = message.get(
                "content"
            )

            content: str | None = None

            # Trường hợp thông thường:
            # content là chuỗi.
            if isinstance(raw_content, str):
                clean_content = raw_content.strip()

                if clean_content:
                    content = clean_content

            # Một số model có thể trả content dưới
            # dạng danh sách các phần nội dung.
            elif isinstance(raw_content, list):
                text_parts: list[str] = []

                for part in raw_content:
                    if isinstance(part, str):
                        text_parts.append(part)
                        continue

                    if not isinstance(part, dict):
                        continue

                    part_text = (
                        part.get("text")
                        or part.get("content")
                    )

                    if part_text:
                        text_parts.append(
                            str(part_text)
                        )

                combined_content = "\n".join(
                    text_parts
                ).strip()

                if combined_content:
                    content = combined_content

            if not content:
                usage = response_data.get(
                    "usage",
                    {},
                )

                reasoning = (
                    message.get("reasoning")
                    or message.get(
                        "reasoning_content"
                    )
                )

                print(
                    "[OpenRouter] Empty content response:"
                )
                print(
                    "MODEL:",
                    response_data.get(
                        "model",
                        self.model,
                    ),
                )
                print(
                    "FINISH REASON:",
                    finish_reason,
                )
                print(
                    "USAGE:",
                    usage,
                )
                print(
                    "MESSAGE KEYS:",
                    list(message.keys()),
                )
                print(
                    "REASONING PRESENT:",
                    bool(reasoning),
                )

                return LLMResult(
                    success=False,
                    provider=self.provider_name,
                    model=response_data.get(
                        "model",
                        self.model,
                    ),
                    error=(
                        "OpenRouter trả về phản hồi "
                        "nhưng không có nội dung văn bản. "
                        f"finish_reason={finish_reason}, "
                        f"message_keys="
                        f"{list(message.keys())}, "
                        f"usage={usage}"
                    ),
                    metadata={
                        "finish_reason": (
                            finish_reason
                        ),
                        "usage": usage,
                        "message_keys": list(
                            message.keys()
                        ),
                        "reasoning_present": bool(
                            reasoning
                        ),
                    },
                )




            return LLMResult(
                success=True,
                content=str(content),
                provider=self.provider_name,
                model=(
                    response_data.get(
                        "model",
                        self.model,
                    )
                ),
                metadata={
                    "structured_output": (
                        response_schema is not None
                    ),
                    "usage": response_data.get(
                        "usage",
                        {},
                    ),
                },
            )

        except httpx.TimeoutException:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "OpenRouter đã vượt quá thời gian "
                    "chờ phản hồi."
                ),
            )

        except httpx.RequestError as error:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "Không thể kết nối OpenRouter: "
                    f"{error}"
                ),
            )

        except httpx.TimeoutException as error:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "OpenRouter phản hồi quá thời gian "
                    f"cho phép ({self.timeout_seconds} giây). "
                    f"Chi tiết: {error}"
                ),
                metadata={
                    "timeout_seconds": (
                        self.timeout_seconds
                    ),
                },
            )

        except httpx.RequestError as error:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=(
                    "Không thể kết nối tới OpenRouter. "
                    f"Chi tiết: {error}"
                ),
            )

        except Exception as error:
            return LLMResult(
                success=False,
                provider=self.provider_name,
                model=self.model,
                error=str(error),
            )
        # except Exception as error:
        #     return LLMResult(
        #         success=False,
        #         provider=self.provider_name,
        #         model=self.model,
        #         error=str(error),
        #     )

    def _read_timeout(self) -> float:
        raw_value = os.getenv(
            "OPENROUTER_TIMEOUT_SECONDS",
            "60",
        )

        try:
            return float(raw_value)
        except (
            TypeError,
            ValueError,
        ):
            return 60.0


    def _read_max_tokens(self) -> int:
        """
        Giới hạn số token OpenRouter được phép sinh.

        Việc đặt giới hạn giúp tránh OpenRouter tính
        theo output tối đa của model và từ chối request
        do không đủ credit.
        """

        raw_value = os.getenv(
            "OPENROUTER_MAX_TOKENS",
            "1800",
        )

        try:
            value = int(raw_value)

            if value <= 0:
                return 1800

            return min(value, 4000)

        except (
            TypeError,
            ValueError,
        ):
            return 1800

    
    