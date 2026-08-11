from app.services.insight.insight_models import (
    InsightObject,
    InsightSeverity,
    RecommendationObject,
)


class RecommendationEngine:
    """
    Chuyển các insight đã phát hiện thành
    khuyến nghị hành động.

    Không gọi LLM.
    Sử dụng luật nghiệp vụ.
    """

    def generate(
        self,
        insights: list[InsightObject],
    ) -> list[RecommendationObject]:

        recommendations: list[
            RecommendationObject
        ] = []

        for insight in insights:
            recommendation = (
                self._build_recommendation(
                    insight
                )
            )

            if recommendation is not None:
                recommendations.append(
                    recommendation
                )

        return sorted(
            recommendations,
            key=self._priority_score,
            reverse=True,
        )

    def _build_recommendation(
        self,
        insight: InsightObject,
    ) -> RecommendationObject | None:

        category = insight.category

        if category == "data_quality":
            return self._for_data_quality(
                insight
            )

        if category == "numeric":
            return self._for_numeric(
                insight
            )

        if category == "categorical":
            return self._for_categorical(
                insight
            )

        if category == "correlation":
            return self._for_correlation(
                insight
            )

        if category == "trend":
            return self._for_trend(
                insight
            )

        return None

    def _for_data_quality(
        self,
        insight: InsightObject,
    ) -> RecommendationObject:

        detector = str(
            insight.metadata.get(
                "detector",
                "",
            )
        )

        if detector == "MissingDetector":
            title = (
                "Ưu tiên xử lý dữ liệu bị thiếu"
            )

            description = (
                "Cần kiểm tra nguyên nhân thiếu dữ liệu "
                "và lựa chọn phương án bổ sung, thay thế "
                "hoặc loại bỏ phù hợp trước khi phân tích."
            )

            actions = [
                (
                    "Xác định các dòng và cột bị thiếu."
                ),
                (
                    "Kiểm tra dữ liệu có thể bổ sung "
                    "từ nguồn gốc hay không."
                ),
                (
                    "Chỉ áp dụng điền giá trị thay thế "
                    "khi có cơ sở nghiệp vụ."
                ),
            ]

        elif detector == "DuplicateDetector":
            title = (
                "Kiểm tra và loại bỏ dữ liệu trùng lặp"
            )

            description = (
                "Dữ liệu trùng có thể làm sai lệch "
                "thống kê, KPI và kết quả phân tích."
            )

            actions = [
                (
                    "Xác định khóa định danh của bản ghi."
                ),
                (
                    "So sánh các dòng trùng trước khi xóa."
                ),
                (
                    "Lưu lại quy tắc loại bỏ dữ liệu trùng."
                ),
            ]

        elif detector == "NegativeDetector":
            title = (
                "Xác minh các giá trị âm bất thường"
            )

            description = (
                "Cần đối chiếu ý nghĩa nghiệp vụ của "
                "cột trước khi kết luận giá trị âm là lỗi."
            )

            actions = [
                (
                    "Kiểm tra đơn vị và ý nghĩa của cột."
                ),
                (
                    "Đối chiếu dữ liệu với nguồn ban đầu."
                ),
                (
                    "Thiết lập ràng buộc dữ liệu nếu "
                    "giá trị âm không hợp lệ."
                ),
            ]

        else:
            title = (
                "Kiểm tra chất lượng dữ liệu"
            )

            description = (
                "Cần xử lý vấn đề chất lượng dữ liệu "
                "trước khi sử dụng kết quả phân tích."
            )

            actions = [
                (
                    "Xác minh dữ liệu với nguồn ban đầu."
                ),
                (
                    "Làm sạch dữ liệu theo quy tắc "
                    "nghiệp vụ."
                ),
            ]

        return self._create_recommendation(
            insight=insight,
            title=title,
            description=description,
            actions=actions,
        )

    def _for_numeric(
        self,
        insight: InsightObject,
    ) -> RecommendationObject:

        detector = str(
            insight.metadata.get(
                "detector",
                "",
            )
        )

        if detector == "OutlierDetector":
            title = (
                "Phân tích các giá trị ngoại lệ"
            )

            description = (
                "Không nên tự động xóa ngoại lệ. "
                "Cần xác định đây là lỗi dữ liệu hay "
                "một trường hợp nghiệp vụ đặc biệt."
            )

            actions = [
                (
                    "Kiểm tra các bản ghi ngoại lệ."
                ),
                (
                    "So sánh với phân phối dữ liệu chung."
                ),
                (
                    "Ghi nhận ngoại lệ hợp lệ thành "
                    "tri thức nghiệp vụ."
                ),
            ]

        elif detector == "SkewnessDetector":
            title = (
                "Điều chỉnh phương pháp phân tích "
                "cho dữ liệu phân phối lệch"
            )

            description = (
                "Phân phối lệch có thể làm giá trị "
                "trung bình không đại diện tốt cho dữ liệu."
            )

            actions = [
                (
                    "Bổ sung median và percentile "
                    "khi báo cáo."
                ),
                (
                    "Cân nhắc biến đổi logarithm "
                    "nếu xây dựng mô hình."
                ),
                (
                    "Kiểm tra tác động của ngoại lệ."
                ),
            ]

        else:
            title = (
                "Kiểm tra đặc điểm dữ liệu số"
            )

            description = (
                "Nên phân tích thêm phân phối và "
                "các giá trị bất thường của biến số."
            )

            actions = [
                (
                    "Xem xét biểu đồ phân phối."
                ),
                (
                    "Đối chiếu với ngưỡng nghiệp vụ."
                ),
            ]

        return self._create_recommendation(
            insight=insight,
            title=title,
            description=description,
            actions=actions,
        )

    def _for_categorical(
        self,
        insight: InsightObject,
    ) -> RecommendationObject:

        detector = str(
            insight.metadata.get(
                "detector",
                "",
            )
        )

        if detector == "DominantCategoryDetector":
            title = (
                "Đánh giá sự phụ thuộc vào nhóm "
                "chiếm ưu thế"
            )

            description = (
                "Một nhóm chiếm tỷ trọng quá lớn có thể "
                "làm dữ liệu mất cân bằng và ảnh hưởng "
                "đến kết luận phân tích."
            )

            actions = [
                (
                    "So sánh kết quả giữa nhóm chiếm "
                    "ưu thế và các nhóm còn lại."
                ),
                (
                    "Kiểm tra nguyên nhân nhóm này "
                    "chiếm tỷ trọng cao."
                ),
                (
                    "Cân nhắc phân tích phân tầng."
                ),
            ]

        else:
            title = (
                "Kiểm tra các nhóm hiếm"
            )

            description = (
                "Nhóm có tần suất thấp có thể là dữ liệu "
                "đặc biệt, lỗi nhập liệu hoặc trường hợp "
                "nghiệp vụ cần quan tâm."
            )

            actions = [
                (
                    "Xác minh tên và giá trị của nhóm hiếm."
                ),
                (
                    "Không gộp nhóm nếu chưa hiểu ý nghĩa."
                ),
                (
                    "Theo dõi riêng các nhóm có giá trị "
                    "nghiệp vụ quan trọng."
                ),
            ]

        return self._create_recommendation(
            insight=insight,
            title=title,
            description=description,
            actions=actions,
        )

    def _for_correlation(
        self,
        insight: InsightObject,
    ) -> RecommendationObject:

        first_column = str(
            insight.metadata.get(
                "first_column",
                "biến thứ nhất",
            )
        )

        second_column = str(
            insight.metadata.get(
                "second_column",
                "biến thứ hai",
            )
        )

        direction = str(
            insight.metadata.get(
                "direction",
                "",
            )
        )

        if direction == "positive":
            relationship_text = (
                "biến động cùng chiều"
            )
        else:
            relationship_text = (
                "biến động ngược chiều"
            )

        return self._create_recommendation(
            insight=insight,
            title=(
                f"Phân tích sâu mối quan hệ giữa "
                f"{first_column} và {second_column}"
            ),
            description=(
                f"Hai biến có xu hướng "
                f"{relationship_text}. "
                f"Nên dùng biểu đồ phân tán và phân tích "
                f"bổ sung trước khi đưa ra quyết định. "
                f"Tương quan không chứng minh quan hệ "
                f"nhân quả."
            ),
            actions=[
                (
                    "Vẽ scatter plot để kiểm tra "
                    "hình dạng mối quan hệ."
                ),
                (
                    "Kiểm tra ngoại lệ có làm thay đổi "
                    "hệ số tương quan hay không."
                ),
                (
                    "Phân tích thêm các yếu tố trung gian."
                ),
            ],
        )

    def _for_trend(
        self,
        insight: InsightObject,
    ) -> RecommendationObject:

        direction = str(
            insight.metadata.get(
                "direction",
                "",
            )
        )

        numeric_column = str(
            insight.metadata.get(
                "numeric_column",
                "chỉ số",
            )
        )

        if direction == "decreasing":
            title = (
                f"Ưu tiên phân tích nguyên nhân "
                f"{numeric_column} suy giảm"
            )

            description = (
                f"{numeric_column} đang có xu hướng giảm. "
                f"Cần phân tích theo nhóm, thời gian và "
                f"các yếu tố liên quan để xác định "
                f"nguyên nhân."
            )

            actions = [
                (
                    "So sánh với giai đoạn trước."
                ),
                (
                    "Phân tích theo phân khúc hoặc nhóm."
                ),
                (
                    "Thiết lập cảnh báo nếu xu hướng "
                    "tiếp tục giảm."
                ),
            ]

        else:
            title = (
                f"Theo dõi xu hướng tăng của "
                f"{numeric_column}"
            )

            description = (
                f"{numeric_column} đang có xu hướng tăng. "
                f"Cần xác định các yếu tố đóng góp để "
                f"duy trì kết quả tích cực."
            )

            actions = [
                (
                    "Xác định giai đoạn tăng mạnh nhất."
                ),
                (
                    "Phân tích các nhóm đóng góp chính."
                ),
                (
                    "Tiếp tục theo dõi để xác nhận "
                    "xu hướng bền vững."
                ),
            ]

        return self._create_recommendation(
            insight=insight,
            title=title,
            description=description,
            actions=actions,
        )

    def _create_recommendation(
        self,
        insight: InsightObject,
        title: str,
        description: str,
        actions: list[str],
    ) -> RecommendationObject:

        return RecommendationObject(
            id=f"recommendation_{insight.id}",
            source_insight_id=insight.id,
            category=insight.category,
            title=title,
            description=description,
            priority=insight.severity,
            actions=actions,
            metadata={
                "source_type": insight.type.value,
                "source_metric": insight.metric,
                "source_value": insight.value,
                "engine": "RecommendationEngine",
            },
        )

    def _priority_score(
        self,
        recommendation: RecommendationObject,
    ) -> int:

        scores = {
            InsightSeverity.LOW: 1,
            InsightSeverity.MEDIUM: 2,
            InsightSeverity.HIGH: 3,
            InsightSeverity.CRITICAL: 4,
        }

        return scores[
            recommendation.priority
        ]