from typing import Any

import pandas as pd


class KPIGenerator:
    """
    Tạo KPI thông minh dựa trên:

    - DataFrame đã được làm sạch
    - Semantic data context
    - Dataset profile

    Không cộng các cột identifier.
    Không tạo KPI cho cột text hoặc dimension.
    """

    MAX_KPIS = 6

    PRIORITY_KEYWORDS = {
        "revenue": 100,
        "sales": 95,
        "profit": 90,
        "income": 85,
        "amount": 80,
        "cost": 75,
        "expense": 75,
        "quantity": 70,
        "qty": 70,
        "orders": 65,
        "customers": 60,
        "discount": 50,
        "rate": 45,
        "score": 40,
    }

    def generate(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None = None,
        dataset_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Tạo danh sách KPI.

        Nếu chưa truyền data_context, fallback về KPI cơ bản.
        """

        if df.empty:
            return []

        if not data_context:
            return self._generate_fallback_kpis(df)

        dataset_type = (
            dataset_profile or {}
        ).get(
            "dataset_type",
            "generic",
        )

        kpis: list[dict[str, Any]] = []

        kpis.extend(
            self._generate_dataset_specific_kpis(
                df=df,
                data_context=data_context,
                dataset_type=dataset_type,
            )
        )

        kpis.extend(
            self._generate_measure_kpis(
                df=df,
                data_context=data_context,
            )
        )

        kpis.extend(
            self._generate_identifier_kpis(
                df=df,
                data_context=data_context,
                dataset_type=dataset_type,
            )
        )

        kpis = self._remove_duplicate_kpis(kpis)

        kpis = self._sort_kpis(kpis)

        return kpis[:self.MAX_KPIS]

    def _generate_dataset_specific_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
        dataset_type: str,
    ) -> list[dict[str, Any]]:
        if dataset_type == "sales":
            return self._generate_sales_kpis(
                df=df,
                data_context=data_context,
            )

        if dataset_type == "customer":
            return self._generate_customer_kpis(
                df=df,
                data_context=data_context,
            )

        if dataset_type == "inventory":
            return self._generate_inventory_kpis(
                df=df,
                data_context=data_context,
            )

        if dataset_type == "human_resources":
            return self._generate_hr_kpis(
                df=df,
                data_context=data_context,
            )

        return []

    def _generate_sales_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = []

        revenue_column = self._find_column(
            data_context=data_context,
            keywords={
                "revenue",
                "sales",
                "amount",
                "total_amount",
                "total_sales",
            },
            roles={"measure"},
        )

        if revenue_column:
            revenue_value = self._safe_sum(
                df,
                revenue_column,
            )

            kpis.append({
                "id": "total_revenue",
                "title": "Total Revenue",
                "value": revenue_value,
                "format": "currency",
                "column": revenue_column,
                "aggregation": "sum",
                "priority": 100,
            })

        profit_column = self._find_column(
            data_context=data_context,
            keywords={
                "profit",
                "net_profit",
                "gross_profit",
            },
            roles={"measure"},
        )

        if profit_column:
            kpis.append({
                "id": "total_profit",
                "title": "Total Profit",
                "value": self._safe_sum(
                    df,
                    profit_column,
                ),
                "format": "currency",
                "column": profit_column,
                "aggregation": "sum",
                "priority": 95,
            })

        quantity_column = self._find_column(
            data_context=data_context,
            keywords={
                "quantity",
                "qty",
                "units",
                "order_quantity",
            },
            roles={"measure"},
        )

        if quantity_column:
            kpis.append({
                "id": "total_quantity",
                "title": "Total Quantity",
                "value": self._safe_sum(
                    df,
                    quantity_column,
                ),
                "format": "number",
                "column": quantity_column,
                "aggregation": "sum",
                "priority": 85,
            })

        order_column = self._find_column(
            data_context=data_context,
            keywords={
                "order_id",
                "order_number",
                "invoice_id",
                "invoice_number",
            },
            roles={"identifier"},
        )

        if order_column:
            order_count = self._safe_nunique(
                df,
                order_column,
            )

            kpis.append({
                "id": "total_orders",
                "title": "Total Orders",
                "value": order_count,
                "format": "integer",
                "column": order_column,
                "aggregation": "nunique",
                "priority": 90,
            })

        customer_column = self._find_column(
            data_context=data_context,
            keywords={
                "customer_id",
                "customer_unique_id",
                "client_id",
            },
            roles={"identifier"},
        )

        if customer_column:
            kpis.append({
                "id": "unique_customers",
                "title": "Unique Customers",
                "value": self._safe_nunique(
                    df,
                    customer_column,
                ),
                "format": "integer",
                "column": customer_column,
                "aggregation": "nunique",
                "priority": 80,
            })

        if revenue_column and order_column:
            order_count = self._safe_nunique(
                df,
                order_column,
            )

            revenue_value = self._safe_sum(
                df,
                revenue_column,
            )

            average_order_value = (
                revenue_value / order_count
                if order_count > 0
                else 0
            )

            kpis.append({
                "id": "average_order_value",
                "title": "Average Order Value",
                "value": round(
                    float(average_order_value),
                    2,
                ),
                "format": "currency",
                "column": revenue_column,
                "aggregation": "sum/nunique",
                "priority": 88,
            })

        return kpis

    def _generate_customer_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = []

        customer_column = self._find_column(
            data_context=data_context,
            keywords={
                "customer_id",
                "customer_unique_id",
                "client_id",
            },
            roles={"identifier"},
        )

        if customer_column:
            kpis.append({
                "id": "unique_customers",
                "title": "Unique Customers",
                "value": self._safe_nunique(
                    df,
                    customer_column,
                ),
                "format": "integer",
                "column": customer_column,
                "aggregation": "nunique",
                "priority": 100,
            })

        city_column = self._find_column(
            data_context=data_context,
            keywords={
                "customer_city",
                "city",
                "province",
                "state",
            },
            roles={"dimension"},
        )

        if city_column:
            kpis.append({
                "id": "covered_locations",
                "title": "Covered Locations",
                "value": self._safe_nunique(
                    df,
                    city_column,
                ),
                "format": "integer",
                "column": city_column,
                "aggregation": "nunique",
                "priority": 70,
            })

        return kpis

    def _generate_inventory_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = []

        stock_column = self._find_column(
            data_context=data_context,
            keywords={
                "stock",
                "inventory",
                "quantity",
                "units",
            },
            roles={"measure"},
        )

        if stock_column:
            kpis.append({
                "id": "total_stock",
                "title": "Total Stock",
                "value": self._safe_sum(
                    df,
                    stock_column,
                ),
                "format": "number",
                "column": stock_column,
                "aggregation": "sum",
                "priority": 100,
            })

        product_column = self._find_column(
            data_context=data_context,
            keywords={
                "product_id",
                "sku",
                "item_id",
            },
            roles={"identifier"},
        )

        if product_column:
            kpis.append({
                "id": "unique_products",
                "title": "Unique Products",
                "value": self._safe_nunique(
                    df,
                    product_column,
                ),
                "format": "integer",
                "column": product_column,
                "aggregation": "nunique",
                "priority": 90,
            })

        return kpis

    def _generate_hr_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = []

        employee_column = self._find_column(
            data_context=data_context,
            keywords={
                "employee_id",
                "staff_id",
                "worker_id",
            },
            roles={"identifier"},
        )

        if employee_column:
            kpis.append({
                "id": "total_employees",
                "title": "Total Employees",
                "value": self._safe_nunique(
                    df,
                    employee_column,
                ),
                "format": "integer",
                "column": employee_column,
                "aggregation": "nunique",
                "priority": 100,
            })

        salary_column = self._find_column(
            data_context=data_context,
            keywords={
                "salary",
                "income",
                "wage",
            },
            roles={"measure"},
        )

        if salary_column:
            kpis.append({
                "id": "average_salary",
                "title": "Average Salary",
                "value": self._safe_mean(
                    df,
                    salary_column,
                ),
                "format": "currency",
                "column": salary_column,
                "aggregation": "mean",
                "priority": 90,
            })

        return kpis

    def _generate_measure_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        kpis: list[dict[str, Any]] = []

        for measure in data_context.get(
            "measures",
            [],
        ):
            column_name = measure.get("name")

            if (
                not column_name
                or column_name not in df.columns
            ):
                continue

            aggregation = (
                measure.get("aggregation")
                or "sum"
            )

            semantic_type = measure.get(
                "semantic_type",
                "measure",
            )

            if aggregation == "mean":
                value = self._safe_mean(
                    df,
                    column_name,
                )
            else:
                value = self._safe_sum(
                    df,
                    column_name,
                )

            kpis.append({
                "id": self._make_kpi_id(
                    aggregation,
                    column_name,
                ),
                "title": self._make_title(
                    aggregation,
                    column_name,
                ),
                "value": value,
                "format": self._get_format(
                    semantic_type
                ),
                "column": column_name,
                "aggregation": aggregation,
                "priority": self._get_priority(
                    column_name
                ),
            })

        return kpis

    def _generate_identifier_kpis(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any],
        dataset_type: str,
    ) -> list[dict[str, Any]]:
        if dataset_type not in {
            "customer",
            "inventory",
            "human_resources",
            "generic",
        }:
            return []

        kpis: list[dict[str, Any]] = []

        for identifier in data_context.get(
            "identifiers",
            [],
        ):
            column_name = identifier.get("name")

            if (
                not column_name
                or column_name not in df.columns
            ):
                continue

            kpis.append({
                "id": f"unique_{column_name}",
                "title": (
                    "Unique "
                    + self._format_column_name(
                        column_name
                    )
                ),
                "value": self._safe_nunique(
                    df,
                    column_name,
                ),
                "format": "integer",
                "column": column_name,
                "aggregation": "nunique",
                "priority": 45,
            })

        return kpis

    def _generate_fallback_kpis(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "total_rows",
                "title": "Rows",
                "value": int(len(df)),
                "format": "integer",
                "column": None,
                "aggregation": "count",
                "priority": 10,
            },
            {
                "id": "total_columns",
                "title": "Columns",
                "value": int(len(df.columns)),
                "format": "integer",
                "column": None,
                "aggregation": "count",
                "priority": 10,
            },
        ]

    def _find_column(
        self,
        data_context: dict[str, Any],
        keywords: set[str],
        roles: set[str],
    ) -> str | None:
        for column in data_context.get(
            "columns",
            [],
        ):
            if column.get("role") not in roles:
                continue

            name = column.get("name", "")
            normalized_name = column.get(
                "normalized_name",
                "",
            )

            if normalized_name in keywords:
                return name

            tokens = set(
                normalized_name.split("_")
            )

            for keyword in keywords:
                keyword_tokens = set(
                    keyword.split("_")
                )

                if keyword_tokens.issubset(tokens):
                    return name

        return None

    def _safe_sum(
        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> int | float:
        series = pd.to_numeric(
            df[column_name],
            errors="coerce",
        )

        value = series.sum()

        return self._json_number(value)

    def _safe_mean(
        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> int | float:
        series = pd.to_numeric(
            df[column_name],
            errors="coerce",
        )

        value = series.mean()

        if pd.isna(value):
            return 0

        return round(
            float(value),
            2,
        )

    def _safe_nunique(
        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> int:
        return int(
            df[column_name].nunique(
                dropna=True
            )
        )

    def _json_number(
        self,
        value: Any,
    ) -> int | float:
        if pd.isna(value):
            return 0

        numeric_value = float(value)

        if numeric_value.is_integer():
            return int(numeric_value)

        return round(
            numeric_value,
            2,
        )

    def _get_format(
        self,
        semantic_type: str,
    ) -> str:
        if semantic_type == "currency":
            return "currency"

        if semantic_type == "percentage":
            return "percentage"

        if semantic_type == "quantity":
            return "number"

        return "number"

    def _get_priority(
        self,
        column_name: str,
    ) -> int:
        normalized_name = (
            column_name
            .strip()
            .lower()
        )

        tokens = set(
            normalized_name.split("_")
        )

        priority = 30

        for keyword, score in (
            self.PRIORITY_KEYWORDS.items()
        ):
            if (
                keyword == normalized_name
                or keyword in tokens
            ):
                priority = max(
                    priority,
                    score,
                )

        return priority

    def _make_kpi_id(
        self,
        aggregation: str,
        column_name: str,
    ) -> str:
        normalized_name = (
            column_name
            .strip()
            .lower()
            .replace(" ", "_")
        )

        return f"{aggregation}_{normalized_name}"

    def _make_title(
        self,
        aggregation: str,
        column_name: str,
    ) -> str:
        prefix = (
            "Average"
            if aggregation == "mean"
            else "Total"
        )

        return (
            f"{prefix} "
            f"{self._format_column_name(column_name)}"
        )

    def _format_column_name(
        self,
        column_name: str,
    ) -> str:
        return (
            column_name
            .replace("_", " ")
            .strip()
            .title()
        )

    def _remove_duplicate_kpis(
        self,
        kpis: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique_kpis: list[dict[str, Any]] = []

        used_ids: set[str] = set()
        used_pairs: set[tuple[Any, Any]] = set()

        for kpi in kpis:
            kpi_id = kpi.get("id")

            pair = (
                kpi.get("column"),
                kpi.get("aggregation"),
            )

            if kpi_id in used_ids:
                continue

            if pair in used_pairs:
                continue

            used_ids.add(kpi_id)
            used_pairs.add(pair)
            unique_kpis.append(kpi)

        return unique_kpis

    def _sort_kpis(
        self,
        kpis: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return sorted(
            kpis,
            key=lambda item: item.get(
                "priority",
                0,
            ),
            reverse=True,
        )