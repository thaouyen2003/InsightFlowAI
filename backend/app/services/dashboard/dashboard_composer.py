from typing import Any


class DashboardComposer:
    """
    Chọn lọc và sắp xếp nội dung dashboard.

    Trách nhiệm:
    - Giới hạn KPI và chart.
    - Ưu tiên nội dung có score/priority cao.
    - Loại KPI trùng.
    - Loại chart trùng thông tin.
    - Cân bằng các loại biểu đồ.
    """

    MAX_KPIS = 6
    MAX_CHARTS = 5

    CHART_TYPE_PRIORITY = {
        "line": 100,
        "bar": 90,
        "pie": 75,
        "scatter": 60,
        "histogram": 50,
    }

    def compose(
        self,
        kpis: list[dict[str, Any]],
        charts: list[dict[str, Any]],
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> dict[str, Any]:
        selected_kpis = self._select_kpis(
            kpis=kpis,
            dataset_profile=dataset_profile,
        )

        selected_charts = self._select_charts(
            charts=charts,
            data_context=data_context,
            dataset_profile=dataset_profile,
        )

        layout = self._build_layout(
            selected_kpis=selected_kpis,
            selected_charts=selected_charts,
        )

        return {
            "kpis": selected_kpis,
            "charts": selected_charts,
            "layout": layout,
            "composition_summary": {
                "input_kpi_count": len(kpis),
                "selected_kpi_count": len(
                    selected_kpis
                ),
                "input_chart_count": len(charts),
                "selected_chart_count": len(
                    selected_charts
                ),
                "dataset_type": (
                    dataset_profile.get(
                        "dataset_type",
                        "generic",
                    )
                ),
            },
        }

    def _select_kpis(
        self,
        kpis: list[dict[str, Any]],
        dataset_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not kpis:
            return []

        dataset_type = dataset_profile.get(
            "dataset_type",
            "generic",
        )

        sorted_kpis = sorted(
            kpis,
            key=lambda item: (
                self._dataset_kpi_bonus(
                    kpi=item,
                    dataset_type=dataset_type,
                )
                + item.get("priority", 0)
            ),
            reverse=True,
        )

        selected: list[dict[str, Any]] = []
        used_ids: set[str] = set()
        used_pairs: set[tuple[Any, Any]] = set()

        for kpi in sorted_kpis:
            kpi_id = str(
                kpi.get("id", "")
            )

            pair = (
                kpi.get("column"),
                kpi.get("aggregation"),
            )

            if kpi_id and kpi_id in used_ids:
                continue

            if pair in used_pairs:
                continue

            if self._is_invalid_kpi(kpi):
                continue

            selected.append(kpi)

            if kpi_id:
                used_ids.add(kpi_id)

            used_pairs.add(pair)

            if len(selected) >= self.MAX_KPIS:
                break

        return selected

    def _dataset_kpi_bonus(
        self,
        kpi: dict[str, Any],
        dataset_type: str,
    ) -> int:
        kpi_id = str(
            kpi.get("id", "")
        ).lower()

        bonus = 0

        if dataset_type == "sales":
            preferred_ids = {
                "total_revenue",
                "total_profit",
                "total_orders",
                "unique_customers",
                "average_order_value",
                "total_quantity",
            }

            if kpi_id in preferred_ids:
                bonus += 100

        elif dataset_type == "customer":
            preferred_ids = {
                "unique_customers",
                "covered_locations",
            }

            if kpi_id in preferred_ids:
                bonus += 100

        elif dataset_type == "inventory":
            preferred_ids = {
                "total_stock",
                "unique_products",
            }

            if kpi_id in preferred_ids:
                bonus += 100

        elif dataset_type == "human_resources":
            preferred_ids = {
                "total_employees",
                "average_salary",
            }

            if kpi_id in preferred_ids:
                bonus += 100

        return bonus

    def _is_invalid_kpi(
        self,
        kpi: dict[str, Any],
    ) -> bool:
        value = kpi.get("value")

        if value is None:
            return True

        title = str(
            kpi.get("title", "")
        ).strip()

        if not title:
            return True

        invalid_titles = {
            "Total Sales Channel",
            "Total Sales Rep",
            "Total Customer Id",
            "Total Order Id",
            "Total Product Id",
        }

        if title in invalid_titles:
            return True

        return False

    def _select_charts(
        self,
        charts: list[dict[str, Any]],
        data_context: dict[str, Any],
        dataset_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not charts:
            return []

        dataset_type = dataset_profile.get(
            "dataset_type",
            "generic",
        )

        scored_charts = []

        for chart in charts:
            score = int(
                chart.get("score", 0)
            )

            chart_type = chart.get("type")

            score += self.CHART_TYPE_PRIORITY.get(
                chart_type,
                0,
            )

            score += self._dataset_chart_bonus(
                chart=chart,
                dataset_type=dataset_type,
            )

            enriched_chart = {
                **chart,
                "composer_score": score,
            }

            scored_charts.append(
                enriched_chart
            )

        scored_charts.sort(
            key=lambda item: item.get(
                "composer_score",
                0,
            ),
            reverse=True,
        )

        selected: list[dict[str, Any]] = []

        used_ids: set[str] = set()
        used_information_pairs: set[
            tuple[Any, Any]
        ] = set()

        chart_type_counts: dict[str, int] = {}

        for chart in scored_charts:
            chart_id = str(
                chart.get("id", "")
            )

            chart_type = str(
                chart.get("type", "")
            )

            if not chart_id or not chart_type:
                continue

            if chart_id in used_ids:
                continue

            if not self._has_valid_chart_data(
                chart
            ):
                continue

            information_pair = (
                chart.get("dimension")
                or chart.get("x_axis"),
                chart.get("measure")
                or chart.get("y_axis"),
            )

            if (
                information_pair
                in used_information_pairs
                and chart_type in {
                    "bar",
                    "pie",
                }
            ):
                continue

            type_limit = self._chart_type_limit(
                chart_type
            )

            if (
                chart_type_counts.get(
                    chart_type,
                    0,
                )
                >= type_limit
            ):
                continue

            selected.append(chart)
            used_ids.add(chart_id)

            if chart_type in {
                "bar",
                "pie",
            }:
                used_information_pairs.add(
                    information_pair
                )

            chart_type_counts[chart_type] = (
                chart_type_counts.get(
                    chart_type,
                    0,
                )
                + 1
            )

            if len(selected) >= self.MAX_CHARTS:
                break

        return self._ensure_chart_balance(
            selected=selected,
            all_charts=scored_charts,
        )

    def _dataset_chart_bonus(
        self,
        chart: dict[str, Any],
        dataset_type: str,
    ) -> int:
        chart_type = chart.get("type")
        measure = str(
            chart.get("measure")
            or chart.get("y_axis")
            or ""
        ).lower()

        bonus = 0

        if dataset_type in {
            "sales",
            "finance",
        }:
            if chart_type == "line":
                bonus += 40

            if any(
                keyword in measure
                for keyword in {
                    "revenue",
                    "sales",
                    "profit",
                    "amount",
                }
            ):
                bonus += 30

        if dataset_type == "customer":
            if chart_type == "bar":
                bonus += 30

        if dataset_type == "inventory":
            if any(
                keyword in measure
                for keyword in {
                    "stock",
                    "quantity",
                    "inventory",
                }
            ):
                bonus += 30

        return bonus

    def _has_valid_chart_data(
        self,
        chart: dict[str, Any],
    ) -> bool:
        data = chart.get("data")

        if not isinstance(data, list):
            return False

        return len(data) > 0

    def _chart_type_limit(
        self,
        chart_type: str,
    ) -> int:
        limits = {
            "line": 2,
            "bar": 2,
            "pie": 1,
            "scatter": 1,
            "histogram": 1,
        }

        return limits.get(
            chart_type,
            1,
        )

   
    def _ensure_chart_balance(
        self,
        selected: list[dict[str, Any]],
        all_charts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if len(selected) >= self.MAX_CHARTS:
            return selected

        selected_types = {
            chart.get("type")
            for chart in selected
        }

        preferred_missing_types = [
            chart_type
            for chart_type in [
                "line",
                "bar",
                "pie",
            ]
            if chart_type not in selected_types
        ]

        used_ids = {
            chart.get("id")
            for chart in selected
        }

        used_information_pairs = {
            (
                chart.get("dimension")
                or chart.get("x_axis"),
                chart.get("measure")
                or chart.get("y_axis"),
            )
            for chart in selected
        }

        for preferred_type in preferred_missing_types:
            matching_chart = next(
                (
                    chart
                    for chart in all_charts
                    if (
                        chart.get("type") == preferred_type
                        and chart.get("id") not in used_ids
                        and self._has_valid_chart_data(chart)
                        and (
                            (
                                chart.get("dimension")
                                or chart.get("x_axis"),
                                chart.get("measure")
                                or chart.get("y_axis"),
                            )
                            not in used_information_pairs
                        )
                    )
                ),
                None,
            )

            if matching_chart:
                selected.append(matching_chart)

                used_ids.add(
                    matching_chart.get("id")
                )

                used_information_pairs.add(
                    (
                        matching_chart.get("dimension")
                        or matching_chart.get("x_axis"),
                        matching_chart.get("measure")
                        or matching_chart.get("y_axis"),
                    )
                )

            if len(selected) >= self.MAX_CHARTS:
                break

        return selected[:self.MAX_CHARTS]



    def _build_layout(
        self,
        selected_kpis: list[dict[str, Any]],
        selected_charts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        chart_layout: list[dict[str, Any]] = []

        for index, chart in enumerate(
            selected_charts
        ):
            chart_type = chart.get("type")

            if chart_type == "line":
                column_span = 2
            else:
                column_span = 1

            chart_layout.append({
                "chart_id": chart.get("id"),
                "order": index,
                "column_span": column_span,
            })

        return {
            "kpi_columns": self._get_kpi_columns(
                len(selected_kpis)
            ),
            "chart_columns": 2,
            "chart_layout": chart_layout,
        }

    def _get_kpi_columns(
        self,
        kpi_count: int,
    ) -> int:
        if kpi_count <= 1:
            return 1

        if kpi_count == 2:
            return 2

        if kpi_count <= 4:
            return 4

        return 3