from typing import Any

import pandas as pd


class ChartGenerator:
    """
    Tạo biểu đồ thông minh dựa trên:

    - DataFrame đã được làm sạch
    - Semantic data context
    - Dataset profile

    Không chọn cột đầu tiên một cách ngẫu nhiên.
    Các biểu đồ ứng viên được chấm điểm trước khi tạo.
    """

    MAX_CHARTS = 5
    MAX_CATEGORIES = 15
    MAX_TIME_POINTS = 100

    MEAN_KEYWORDS = {
        "score",
        "gpa",
        "cpa",
        "grade",
        "mark",
        "average",
        "avg",
        "point",
        "rating",
        "rate",
        "percentage",
        "percent",
    }

   
    def generate(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None = None,
        dataset_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if df.empty:
            return []

        if not data_context:
            return self._generate_fallback_charts(df)

        candidates = self._build_candidates(
            df=df,
            data_context=data_context,
            dataset_profile=dataset_profile or {},
        )

        candidates = self._remove_duplicate_candidates(
            candidates
        )

        candidates = sorted(
            candidates,
            key=lambda item: item.get("score", 0),
            reverse=True,
        )

        charts: list[dict[str, Any]] = []

        for candidate in candidates:
            chart = self._materialize_chart(
                df=df,
                candidate=candidate,
            )

            if chart:
                charts.append(chart)

            if len(charts) >= self.MAX_CHARTS:
                break

        return charts
    
    

    def _build_candidates(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        measures = data_context.get(
            "measures",
            [],
        )

        datetime_columns = data_context.get(
            "datetime_columns",
            [],
        )

        categorical_columns = data_context.get(
            "categorical_columns",
            [],
        )

        dataset_type = dataset_profile.get(
            "dataset_type",
            "generic",
        )

        # ==========================================
        # 1. LINE CHART VÀ AREA CHART
        # ==========================================

        for datetime_column in datetime_columns:
            datetime_name = datetime_column.get("name")

            if not datetime_name:
                continue

            if datetime_name not in df.columns:
                continue

            for measure in measures:
                measure_name = measure.get("name")

                if not measure_name:
                    continue

                if measure_name not in df.columns:
                    continue

                aggregation = self._resolve_aggregation(
                    measure_name=measure_name,
                    default_aggregation=measure.get(
                        "aggregation"
                    ),
                )

                score = 90

                if dataset_type in {
                    "sales",
                    "finance",
                }:
                    score += 10

                if measure.get(
                    "semantic_type"
                ) == "currency":
                    score += 10

                candidates.append({
                    "type": "line",
                    "dimension": datetime_name,
                    "measure": measure_name,
                    "aggregation": aggregation,
                    "score": score,
                    "reason": (
                        "Datetime dimension kết hợp "
                        "với measure phù hợp để "
                        "thể hiện xu hướng."
                    ),
                })

                if (
                    dataset_type in {
                        "sales",
                        "finance",
                    }
                    or measure.get(
                        "semantic_type"
                    ) == "currency"
                ):
                    candidates.append({
                        "type": "area",
                        "dimension": datetime_name,
                        "measure": measure_name,
                        "aggregation": aggregation,
                        "score": score - 4,
                        "reason": (
                            "Dữ liệu thời gian kết hợp "
                            "với giá trị tài chính phù hợp "
                            "biểu đồ miền."
                        ),
                    })

        # ==========================================
        # 2. BAR, PIE VÀ HORIZONTAL BAR
        # ==========================================

        for dimension in categorical_columns:
            dimension_name = dimension.get("name")

            unique_count = dimension.get(
                "unique_count",
                0,
            )

            if not dimension_name:
                continue

            if dimension_name not in df.columns:
                continue

            if unique_count < 2:
                continue

            if unique_count > 30:
                continue

            for measure in measures:
                measure_name = measure.get("name")

                if not measure_name:
                    continue

                if measure_name not in df.columns:
                    continue

                aggregation = self._resolve_aggregation(
                    measure_name=measure_name,
                    default_aggregation=measure.get(
                        "aggregation"
                    ),
                )

                semantic_type = measure.get(
                    "semantic_type"
                )

                base_score = 75

                if semantic_type == "currency":
                    base_score += 5

                # Bar đứng
                if 2 <= unique_count <= 8:
                    candidates.append({
                        "type": "bar",
                        "dimension": dimension_name,
                        "measure": measure_name,
                        "aggregation": aggregation,
                        "score": base_score + 10,
                        "reason": (
                            "Categorical dimension có "
                            "ít nhóm, phù hợp biểu đồ "
                            "cột đứng."
                        ),
                    })

                # Pie
                
                # Horizontal Bar
                if 9 <= unique_count <= 30:
                    candidates.append({
                        "type": "horizontal_bar",
                        "dimension": dimension_name,
                        "measure": measure_name,
                        "aggregation": aggregation,
                        "score": base_score + 12,
                        "reason": (
                            "Categorical dimension có "
                            "nhiều nhóm, phù hợp biểu đồ "
                            "thanh ngang."
                        ),
                    })

        for dimension in categorical_columns:
            dimension_name = dimension.get("name")

            unique_count = dimension.get(
                "unique_count",
                0,
            )

            if not dimension_name:
                continue

            if dimension_name not in df.columns:
                continue

            if unique_count < 2:
                continue

            if unique_count > 30:
                continue

            # Pie chỉ đếm category, không dùng measure.
            if 2 <= unique_count <= 6:
                candidates.append({
                    "type": "pie",
                    "dimension": dimension_name,
                    "measure": None,
                    "aggregation": "count",
                    "score": 86,
                    "reason": (
                        "Category có ít nhóm, phù hợp "
                        "để thể hiện cơ cấu số lượng."
                    ),
                })

            for measure in measures:
                measure_name = measure.get("name")

                if not measure_name:
                    continue

                if measure_name not in df.columns:
                    continue

                aggregation = self._resolve_aggregation(
                    measure_name=measure_name,
                    default_aggregation=measure.get(
                        "aggregation"
                    ),
                )

                semantic_type = measure.get(
                    "semantic_type"
                )

                base_score = 75

                if semantic_type == "currency":
                    base_score += 5

                if 2 <= unique_count <= 8:
                    candidates.append({
                        "type": "bar",
                        "dimension": dimension_name,
                        "measure": measure_name,
                        "aggregation": aggregation,
                        "score": base_score + 10,
                        "reason": (
                            "Categorical dimension có "
                            "ít nhóm, phù hợp biểu đồ "
                            "cột đứng."
                        ),
                    })

                if 9 <= unique_count <= 30:
                    candidates.append({
                        "type": "horizontal_bar",
                        "dimension": dimension_name,
                        "measure": measure_name,
                        "aggregation": aggregation,
                        "score": base_score + 12,
                        "reason": (
                            "Categorical dimension có "
                            "nhiều nhóm, phù hợp biểu đồ "
                            "thanh ngang."
                        ),
                    })
        # ==========================================
        # 3. SCATTER CHART
        # ==========================================

        numeric_measures = [
            measure
            for measure in measures
            if measure.get("name") in df.columns
        ]

        if len(numeric_measures) >= 2:
            first_measure = numeric_measures[0]
            second_measure = numeric_measures[1]

            candidates.append({
                "type": "scatter",
                "x_measure": first_measure["name"],
                "y_measure": second_measure["name"],
                "score": 55,
                "reason": (
                    "Hai measure numeric có thể dùng "
                    "để quan sát mối quan hệ."
                ),
            })

        # ==========================================
        # 4. HISTOGRAM
        # ==========================================

        for measure in numeric_measures[:2]:
            candidates.append({
                "type": "histogram",
                "measure": measure["name"],
                "score": 45,
                "reason": (
                    "Một measure numeric phù hợp "
                    "để xem phân phối."
                ),
            })

        return candidates

   
    def _materialize_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        chart_type = candidate.get("type")

        try:
            if chart_type == "line":
                return self._generate_line_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "area":
                return self._generate_area_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "bar":
                return self._generate_bar_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "horizontal_bar":
                return self._generate_horizontal_bar_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "pie":
                return self._generate_pie_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "scatter":
                return self._generate_scatter_chart(
                    df=df,
                    candidate=candidate,
                )

            if chart_type == "histogram":
                return self._generate_histogram(
                    df=df,
                    candidate=candidate,
                )

        except Exception as error:
            print(
                "Chart materialization failed:",
                chart_type,
                str(error),
            )

        return None

    def _generate_line_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        dimension = candidate["dimension"]
        measure = candidate["measure"]
        aggregation = candidate["aggregation"]

        if (
            dimension not in df.columns
            or measure not in df.columns
        ):
            return None

        working_df = df[
            [dimension, measure]
        ].copy()

        working_df[dimension] = pd.to_datetime(
            working_df[dimension],
            errors="coerce",
        )

        working_df[measure] = pd.to_numeric(
            working_df[measure],
            errors="coerce",
        )

        working_df = working_df.dropna()

        if working_df.empty:
            return None

        working_df["period"] = (
            working_df[dimension]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        grouped = self._aggregate(
            working_df,
            group_column="period",
            measure_column=measure,
            aggregation=aggregation,
        )

        grouped = grouped.sort_values(
            "period"
        ).head(self.MAX_TIME_POINTS)

        data = [
            {
                "x": row["period"].strftime(
                    "%Y-%m-%d"
                ),
                "y": self._json_number(
                    row[measure]
                ),
            }
            for _, row in grouped.iterrows()
        ]

        if not data:
            return None

        return {
            "id": (
                f"line_{dimension}_{measure}"
            ),
            "type": "line",
            "title": (
                f"{self._format_name(measure)} "
                "Trend Over Time"
            ),
            "x_axis": dimension,
            "y_axis": measure,
            "aggregation": aggregation,
            "data": data,
            "score": candidate["score"],
            "reason": candidate["reason"],
        }
    
    def _generate_area_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        dimension = candidate["dimension"]
        measure = candidate["measure"]
        aggregation = candidate["aggregation"]

        if (
            dimension not in df.columns
            or measure not in df.columns
        ):
            return None

        working_df = df[
            [dimension, measure]
        ].copy()

        working_df[dimension] = pd.to_datetime(
            working_df[dimension],
            errors="coerce",
        )

        working_df[measure] = pd.to_numeric(
            working_df[measure],
            errors="coerce",
        )

        working_df = working_df.dropna(
            subset=[
                dimension,
                measure,
            ]
        )

        if working_df.empty:
            return None

        working_df["period"] = (
            working_df[dimension]
            .dt.to_period("M")
            .dt.to_timestamp()
        )

        grouped = self._aggregate(
            working_df,
            group_column="period",
            measure_column=measure,
            aggregation=aggregation,
        )

        grouped = grouped.sort_values(
            "period"
        ).head(self.MAX_TIME_POINTS)

        data = [
            {
                "x": row["period"].strftime(
                    "%Y-%m-%d"
                ),
                "y": self._json_number(
                    row[measure]
                ),
            }
            for _, row in grouped.iterrows()
        ]

        if not data:
            return None

        return {
            "id": (
                f"area_{dimension}_{measure}"
            ),
            "type": "area",
            "title": (
                f"{self._format_name(measure)} "
                "Area Trend Over Time"
            ),
            "x_axis": dimension,
            "y_axis": measure,
            "aggregation": aggregation,
            "data": data,
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def _generate_bar_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        dimension = candidate["dimension"]
        measure = candidate["measure"]
        aggregation = candidate["aggregation"]

        title = self._make_measure_chart_title(
            measure=measure,
            dimension=dimension,
            aggregation=aggregation,
        )

        if (
            dimension not in df.columns
            or measure not in df.columns
        ):
            return None

        working_df = df[
            [dimension, measure]
        ].copy()

        working_df[measure] = pd.to_numeric(
            working_df[measure],
            errors="coerce",
        )

        working_df = working_df.dropna()

        if working_df.empty:
            return None

        grouped = self._aggregate(
            working_df,
            group_column=dimension,
            measure_column=measure,
            aggregation=aggregation,
        )

        grouped = grouped.sort_values(
            measure,
            ascending=False,
        ).head(self.MAX_CATEGORIES)

        data = [
            {
                "label": str(row[dimension]),
                "value": self._json_number(
                    row[measure]
                ),
            }
            for _, row in grouped.iterrows()
        ]

        if not data:
            return None

        return {
            "id": (
                f"bar_{dimension}_{measure}"
            ),
            "type": "bar",
            "title": (
                f"{self._format_name(measure)} "
                f"by {self._format_name(dimension)}"
            ),
            "dimension": dimension,
            "measure": measure,
            "aggregation": aggregation,
            "data": data,
            "x": [
                item["label"]
                for item in data
            ],
            "y": [
                item["value"]
                for item in data
            ],
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def _make_measure_chart_title(
        self,
        measure: str,
        dimension: str,
        aggregation: str,
    ) -> str:
        normalized_measure = (
            str(measure)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        measure_display = self._format_name(
            measure
        )

        dimension_display = self._format_name(
            dimension
        )

        if (
            aggregation == "mean"
            and normalized_measure == "cpa"
        ):
            return (
                f"Điểm CPA trung bình theo "
                f"{dimension_display}"
            )

        if (
            aggregation == "mean"
            and normalized_measure == "gpa"
        ):
            return (
                f"Điểm GPA trung bình theo "
                f"{dimension_display}"
            )

        if aggregation == "mean":
            return (
                f"{measure_display} trung bình theo "
                f"{dimension_display}"
            )

        return (
            f"{measure_display} theo "
            f"{dimension_display}"
        )

    
    def _generate_horizontal_bar_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        dimension = candidate["dimension"]
        measure = candidate["measure"]
        aggregation = candidate["aggregation"]

        if (
            dimension not in df.columns
            or measure not in df.columns
        ):
            return None

        working_df = df[
            [dimension, measure]
        ].copy()

        working_df[measure] = pd.to_numeric(
            working_df[measure],
            errors="coerce",
        )

        working_df = working_df.dropna(
            subset=[
                dimension,
                measure,
            ]
        )

        if working_df.empty:
            return None

        grouped = self._aggregate(
            working_df,
            group_column=dimension,
            measure_column=measure,
            aggregation=aggregation,
        )

        grouped = grouped.sort_values(
            measure,
            ascending=False,
        ).head(self.MAX_CATEGORIES)

        data = [
            {
                "label": str(row[dimension]),
                "value": self._json_number(
                    row[measure]
                ),
            }
            for _, row in grouped.iterrows()
        ]

        if not data:
            return None

        return {
            "id": (
                f"horizontal_bar_"
                f"{dimension}_{measure}"
            ),
            "type": "horizontal_bar",
           "title": title,
            "dimension": dimension,
            "measure": measure,
            "aggregation": aggregation,
            "data": data,
            "x": [
                item["label"]
                for item in data
            ],
            "y": [
                item["value"]
                for item in data
            ],
            "x_axis": measure,
            "y_axis": dimension,
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def _generate_pie_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        dimension = candidate["dimension"]
        measure = candidate["measure"]
        aggregation = candidate["aggregation"]

        if (
            dimension not in df.columns
            or measure not in df.columns
        ):
            return None

        working_df = df[
            [dimension, measure]
        ].copy()

        working_df[measure] = pd.to_numeric(
            working_df[measure],
            errors="coerce",
        )

        working_df = working_df.dropna()

        if working_df.empty:
            return None

        grouped = self._aggregate(
            working_df,
            group_column=dimension,
            measure_column=measure,
            aggregation=aggregation,
        )

        grouped = grouped.sort_values(
            measure,
            ascending=False,
        ).head(6)

        data = [
            {
                "name": str(row[dimension]),
                "value": self._json_number(
                    row[measure]
                ),
            }
            for _, row in grouped.iterrows()
        ]

        if not data:
            return None

        return {
            "id": (
                f"pie_{dimension}_{measure}"
            ),
            "type": "pie",
            "title": (
                f"{self._format_name(measure)} "
                f"Distribution by "
                f"{self._format_name(dimension)}"
            ),
            "dimension": dimension,
            "measure": measure,
            "aggregation": aggregation,
            "data": data,
            "labels": [
                item["name"]
                for item in data
            ],
            "values": [
                item["value"]
                for item in data
            ],
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def generate_horizontal_bar_chart(
        self,
        df: pd.DataFrame
    ):
        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns

        for column in categorical_columns:
            unique_count = df[column].nunique(
                dropna=True
            )

            # Bỏ qua cột ID
            if column.lower().endswith("_id"):
                continue

            # Horizontal Bar phù hợp với khoảng 6–20 nhóm
            if 6 <= unique_count <= 20:
                top_values = (
                    df[column]
                    .dropna()
                    .astype(str)
                    .value_counts()
                    .head(10)
                )

                data = [
                    {
                        "name": str(name),
                        "value": int(value),
                    }
                    for name, value in top_values.items()
                ]

                return {
                    "type": "horizontal_bar",
                    "title": f"Top {column.replace('_', ' ').title()}",
                    "x_axis": "Count",
                    "y_axis": column,
                    "data": data,
                }

        return None

    def _generate_scatter_chart(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        x_measure = candidate["x_measure"]
        y_measure = candidate["y_measure"]

        if (
            x_measure not in df.columns
            or y_measure not in df.columns
        ):
            return None

        working_df = df[
            [x_measure, y_measure]
        ].copy()

        working_df[x_measure] = pd.to_numeric(
            working_df[x_measure],
            errors="coerce",
        )

        working_df[y_measure] = pd.to_numeric(
            working_df[y_measure],
            errors="coerce",
        )

        working_df = (
            working_df
            .dropna()
            .head(200)
        )

        if working_df.empty:
            return None

        data = [
            {
                "x": self._json_number(
                    row[x_measure]
                ),
                "y": self._json_number(
                    row[y_measure]
                ),
            }
            for _, row in working_df.iterrows()
        ]

        return {
            "id": (
                f"scatter_{x_measure}_{y_measure}"
            ),
            "type": "scatter",
            "title": (
                f"{self._format_name(y_measure)} "
                f"vs {self._format_name(x_measure)}"
            ),
            "x_axis": x_measure,
            "y_axis": y_measure,
            "data": data,
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def _generate_histogram(
        self,
        df: pd.DataFrame,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        measure = candidate["measure"]

        if measure not in df.columns:
            return None

        series = pd.to_numeric(
            df[measure],
            errors="coerce",
        ).dropna()

        if series.empty:
            return None

        bins = min(
            10,
            max(
                3,
                int(series.nunique() ** 0.5),
            ),
        )

        categories = pd.cut(
            series,
            bins=bins,
            duplicates="drop",
        )

        counts = categories.value_counts(
            sort=False
        )

        data = [
            {
                "label": str(interval),
                "value": int(count),
            }
            for interval, count in counts.items()
        ]

        return {
            "id": f"histogram_{measure}",
            "type": "histogram",
            "title": (
                f"{self._format_name(measure)} "
                "Distribution"
            ),
            "measure": measure,
            "data": data,
            "score": candidate["score"],
            "reason": candidate["reason"],
        }

    def _aggregate(
        self,
        df: pd.DataFrame,
        group_column: str,
        measure_column: str,
        aggregation: str,
    ) -> pd.DataFrame:
        allowed_aggregations = {
            "sum",
            "mean",
            "count",
            "min",
            "max",
            "median",
        }

        if aggregation not in allowed_aggregations:
            aggregation = "sum"

        grouped = (
            df.groupby(
                group_column,
                dropna=False,
            )[measure_column]
            .agg(aggregation)
            .reset_index()
        )

        return grouped

    def _remove_duplicate_candidates(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique_candidates: list[
            dict[str, Any]
        ] = []

        used_keys: set[tuple[Any, ...]] = set()

        for candidate in candidates:
            key = (
                candidate.get("type"),
                candidate.get("dimension"),
                candidate.get("measure"),
                candidate.get("x_measure"),
                candidate.get("y_measure"),
            )

            if key in used_keys:
                continue

            used_keys.add(key)
            unique_candidates.append(
                candidate
            )

        return unique_candidates

    def _generate_fallback_charts(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        numeric_columns = list(
            df.select_dtypes(
                include="number"
            ).columns
        )

        if not numeric_columns:
            return []

        charts: list[dict[str, Any]] = []

        for measure in numeric_columns[:2]:
            candidate = {
                "type": "histogram",
                "measure": measure,
                "score": 10,
                "reason": (
                    "Fallback chart do chưa có "
                    "semantic context."
                ),
            }

            chart = self._generate_histogram(
                df=df,
                candidate=candidate,
            )

            if chart:
                charts.append(chart)

        return charts

    def _json_number(
        self,
        value: Any,
    ) -> int | float:
        if pd.isna(value):
            return 0

        number = float(value)

        if number.is_integer():
            return int(number)

        return round(number, 2)

    def _format_name(
        self,
        column_name: str,
    ) -> str:
        return (
            column_name
            .replace("_", " ")
            .strip()
            .title()
        )

    def _infer_measure_aggregation(
        self,
        column_name: str,
        default_aggregation: str = "sum",
    ) -> str:
        normalized_name = self._normalize_name(
            column_name
        )

        tokens = set(
            normalized_name.split("_")
        )

        if tokens & self.MEAN_KEYWORDS:
            return "mean"

        return default_aggregation

    def _resolve_aggregation(
        self,
        measure_name: str,
        default_aggregation: str | None,
    ) -> str:
        """
        Xác định phép tổng hợp phù hợp cho measure.

        GPA, CPA, score, rate... luôn dùng mean,
        không được cộng tổng.
        """

        normalized_name = (
            str(measure_name)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        tokens = set(
            normalized_name.split("_")
        )

        if tokens & self.MEAN_KEYWORDS:
            return "mean"

        allowed_aggregations = {
            "sum",
            "mean",
            "median",
            "min",
            "max",
            "count",
        }

        if default_aggregation in allowed_aggregations:
            return str(default_aggregation)

        return "sum"