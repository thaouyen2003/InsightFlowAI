"""
Semantic Detector

Nhiệm vụ:
- Nhận diện ý nghĩa của cột dựa trên tên cột.
- Không đọc dữ liệu trong cột.
- Chỉ phân tích tên cột.
"""


import re


class SemanticDetector:

    # Dictionary các từ khóa

    KEYWORDS = {

        "identifier": [
            "id",
            "_id",
            "uuid",
            "key",
        ],

        "date": [
            "date",
            "time",
            "timestamp",
            "created",
            "updated",
            "purchase",
        ],

        "currency": [
            "price",
            "payment",
            "amount",
            "sales",
            "revenue",
            "profit",
            "cost",
            "value",
        ],

        "customer": [
            "customer",
            "client",
            "buyer",
            "user",
        ],

        "product": [
            "product",
            "item",
            "sku",
            "category",
        ],

        "location": [
            "city",
            "state",
            "country",
            "province",
            "zip",
            "postal",
            "address",
        ],

        "email": [
            "email",
            "mail",
        ],

        "phone": [
            "phone",
            "mobile",
            "telephone",
        ]
    }


    # Hàm chính

    @classmethod
    def detect(cls, column_name: str) -> str:
        """
        Trả về semantic type của tên cột.

        Example
        -------
        customer_id -> identifier
        payment_value -> currency
        """

        column_name = cls.normalize(column_name)

        for semantic_type, keywords in cls.KEYWORDS.items():

            for keyword in keywords:

                if keyword in column_name:
                    return semantic_type

        return "unknown"

    # Chuẩn hóa tên cột

    @staticmethod
    def normalize(text: str) -> str:

        text = text.lower().strip()

        text = re.sub(r"[\s\-]+", "_", text)

        return text