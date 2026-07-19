import os

from dotenv import load_dotenv
from openai import OpenAI


class LLMInsightWriter:
    """
    Viết lại insight bằng LLM.

    Đây là bản kiểm tra khởi tạo trước khi
    bổ sung toàn bộ logic rewrite.
    """

    def __init__(self):
        load_dotenv(".env")

        self.enabled = (
            os.getenv(
                "ENABLE_LLM_INSIGHTS",
                "false",
            ).lower()
            == "true"
        )

        self.api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6",
        )

        self.client: OpenAI | None = None

        if self.enabled and self.api_key:
            self.client = OpenAI(
                api_key=self.api_key
            )