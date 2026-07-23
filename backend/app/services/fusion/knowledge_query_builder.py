from typing import Any


class KnowledgeQueryBuilder:
    """
    Chuyển các phát hiện từ dữ liệu thành câu hỏi ngắn,
    phù hợp để truy xuất tài liệu trong Knowledge Base.
    """

    CATEGORY_QUERIES = {
        "tot_nghiep": (
            "Điều kiện xét và công nhận tốt nghiệp "
            "của sinh viên là gì?"
        ),
        "hoc_vu": (
            "Điều kiện cảnh báo học vụ và xử lý "
            "kết quả học tập của sinh viên là gì?"
        ),
        "hoc_bong": (
            "Điều kiện xét học bổng khuyến khích "
            "học tập của sinh viên là gì?"
        ),
        "dao_tao": (
            "Quy định về đăng ký học phần, học lại "
            "và số tín chỉ của sinh viên là gì?"
        ),
        "hoc_phi": (
            "Quy định về học phí và nghĩa vụ "
            "thanh toán của sinh viên là gì?"
        ),
        "education": (
            "Những quy định đào tạo và học vụ nào "
            "liên quan đến kết quả học tập của sinh viên?"
        ),
    }

    def build(
        self,
        findings: list[Any],
        dataset_name: str | None = None,
        category: str | None = None,
        insight_result: Any | None = None,
    ) -> str:
        """
        Tạo câu hỏi truy xuất tri thức.

        Thứ tự ưu tiên:
        1. Category được truyền vào.
        2. Nội dung findings và tên dataset.
        3. Câu hỏi mặc định.
        """

        normalized_findings = self._normalize_findings(
            findings
        )

        findings_text = " ".join(
            normalized_findings
        ).lower()

        dataset_text = (
            dataset_name or ""
        ).lower()

        searchable_text = (
            f"{dataset_text} {findings_text}"
        )

        normalized_category = (
            category.strip().lower()
            if category
            else None
        )

        if (
            normalized_category
            in self.CATEGORY_QUERIES
        ):
            return self._build_query_with_findings(
                base_query=self.CATEGORY_QUERIES[
                    normalized_category
                ],
                findings=normalized_findings,
            )

        if any(
            keyword in searchable_text
            for keyword in [
                "graduation_status",
                "graduation",
                "tốt nghiệp",
                "đủ điều kiện",
                "chưa đủ",
                "credits_completed",
                "english_standard",
                "it_standard",
            ]
        ):
            base_query = (
                "Điều kiện xét và công nhận tốt nghiệp "
                "của sinh viên là gì?"
            )

            return self._build_query_with_findings(
                base_query=base_query,
                findings=normalized_findings,
            )

        if any(
            keyword in searchable_text
            for keyword in [
                "academic_status",
                "cảnh báo học vụ",
                "gpa",
                "credits_failed",
                "tín chỉ không đạt",
                "điểm trung bình",
            ]
        ):
            base_query = (
                "Điều kiện cảnh báo học vụ và xử lý "
                "kết quả học tập của sinh viên là gì?"
            )

            return self._build_query_with_findings(
                base_query=base_query,
                findings=normalized_findings,
            )

        if any(
            keyword in searchable_text
            for keyword in [
                "scholarship",
                "học bổng",
                "conduct_score",
                "điểm rèn luyện",
            ]
        ):
            base_query = (
                "Điều kiện xét học bổng khuyến khích "
                "học tập của sinh viên là gì?"
            )

            return self._build_query_with_findings(
                base_query=base_query,
                findings=normalized_findings,
            )

        if any(
            keyword in searchable_text
            for keyword in [
                "course_registration",
                "course_code",
                "học phần",
                "học lại",
                "đăng ký học phần",
                "tín chỉ",
            ]
        ):
            base_query = (
                "Quy định về đăng ký học phần, học lại "
                "và số tín chỉ của sinh viên là gì?"
            )

            return self._build_query_with_findings(
                base_query=base_query,
                findings=normalized_findings,
            )

        if any(
            keyword in searchable_text
            for keyword in [
                "tuition",
                "tuition_fee",
                "payment_status",
                "học phí",
                "thanh toán",
            ]
        ):
            base_query = (
                "Quy định về học phí và nghĩa vụ "
                "thanh toán của sinh viên là gì?"
            )

            return self._build_query_with_findings(
                base_query=base_query,
                findings=normalized_findings,
            )

        base_query = (
            "Những quy định đào tạo và học vụ nào "
            "liên quan đến kết quả học tập của sinh viên?"
        )

        return self._build_query_with_findings(
            base_query=base_query,
            findings=normalized_findings,
        )

    def _build_query_with_findings(
        self,
        base_query: str,
        findings: list[str],
    ) -> str:
        """
        Kết hợp câu hỏi chính với tối đa 5 phát hiện dữ liệu.
        """

        if not findings:
            return base_query

        findings_text = "\n".join(
            f"- {finding}"
            for finding in findings[:5]
        )

        return (
            "Dữ liệu đang có các phát hiện sau:\n"
            f"{findings_text}\n\n"
            "Dựa trên tài liệu chính thức, hãy trả lời:\n"
            f"{base_query}"
        )

    def _normalize_findings(
        self,
        findings: list[Any] | None,
    ) -> list[str]:
        normalized: list[str] = []

        if not findings:
            return normalized

        for finding in findings:
            if isinstance(finding, str):
                normalized.append(finding)
                continue

            if isinstance(finding, dict):
                message = (
                    finding.get("message")
                    or finding.get("description")
                    or finding.get("title")
                    or finding.get("summary")
                )

                if message:
                    normalized.append(
                        str(message)
                    )
                else:
                    normalized.append(
                        str(finding)
                    )

                continue

            message = getattr(
                finding,
                "message",
                None,
            )

            if not message:
                message = getattr(
                    finding,
                    "description",
                    None,
                )

            if not message:
                message = getattr(
                    finding,
                    "summary",
                    None,
                )

            if message:
                normalized.append(
                    str(message)
                )
            else:
                normalized.append(
                    str(finding)
                )

        return normalized