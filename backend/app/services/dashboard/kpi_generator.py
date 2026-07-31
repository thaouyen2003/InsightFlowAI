from typing import Any

import pandas as pd


class KPIGenerator:
    """
    Tạo KPI thông minh dựa trên:

    - DataFrame đã được làm sạch
    - Semantic data context
    - Dataset profile
    - Ngữ cảnh nghiệp vụ của dataset

    Không cộng identifier, score, rate hoặc balance
    một cách thiếu ý nghĩa.
    """

    MAX_KPIS = 6

    ADMISSION_SCORE_COLUMNS = {
        "diem_xet_tuyen",
        "điểm_xét_tuyển",
        "tong_diem_xet_tuyen",
        "tổng_điểm_xét_tuyển",
        "admission_score",
        "entrance_score",
    }

    ADMISSION_METHOD_COLUMNS = {
        "phuong_thuc_xet_tuyen",
        "phương_thức_xét_tuyển",
        "admission_method",
        "application_method",
    }



    FINANCE_KEYWORDS = {
        "transaction",
        "payment",
        "account",
        "amount",
        "balance",
        "credit",
        "risk",
        "fee",
        "deposit",
        "withdrawal",
        "loan",
    }

    PRIORITY_KEYWORDS = {
        "revenue": 100,
        "sales": 95,
        "profit": 90,
        "amount": 88,
        "cost": 80,
        "expense": 80,
        "quantity": 75,
        "qty": 75,
        "orders": 70,
        "customers": 65,
        "income": 60,
        "discount": 55,
        "rate": 50,
        "score": 45,
    }

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
        "income",
        "salary",
        "wage",
        "balance",
        "age",
        "admission_score",
        "entrance_score",
        "application_score",
        "admission_points",
        "diem_xet_tuyen",
        "tong_diem_xet_tuyen",
    }

    DISPLAY_NAME = {
        "conduct_score": "Điểm rèn luyện",
        "gpa": "Điểm GPA",
        "cpa": "Điểm CPA",
        "average_score": "Điểm trung bình",
        "final_score": "Điểm cuối kỳ",
        "midterm_score": "Điểm giữa kỳ",
        "grade_point": "Điểm học tập",
        "điểm_xét_tuyển": "Điểm xét tuyển",
        "credits_registered": "Tín chỉ đăng ký",
        "credits_passed": "Tín chỉ đạt",
        "semester": "Học kỳ",
        "student_id": "Sinh viên",
    }

    STUDENT_IDENTIFIER_COLUMNS = {
        "student_id",
        "student_code",
        "student_number",
        "student_no",
        "studentid",
        "mssv",
        "ma_sinh_vien",
        "ma_sv",
    }

    ROW_INDEX_COLUMNS = {
        "stt",
        "index",
        "row_index",
        "row_number",
        "no",
    }

    # DISPLAY_NAME = {

    #     "conduct_score":
    #         "Điểm rèn luyện",

    #     "gpa":
    #         "Điểm GPA",

    #     "credits_passed":
    #         "Tín chỉ đạt",

    #     "credits_registered":
    #         "Tín chỉ đăng ký",

    #     "mandatory_courses_remaining":
    #         "Học phần bắt buộc còn thiếu",

    #     "semester":
    #         "Học kỳ",

    #     "student_id":
    #         "Sinh viên",

    #     "customer_id":
    #         "Khách hàng",

    #     "customer":
    #         "Khách hàng",

    #     "revenue":
    #         "Doanh thu",

    #     "sales":
    #         "Doanh số",

    #     "profit":
    #         "Lợi nhuận",

    #     "cost":
    #         "Chi phí",

    #     "payment_value":
    #         "Giá trị thanh toán",

    #     "amount":
    #         "Giá trị",

    #     "quantity":
    #         "Số lượng",

    #     "price":
    #         "Đơn giá",

    # }

    def generate(
        self,
        df: pd.DataFrame,
        data_context: dict[str, Any] | None = None,
        dataset_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Tạo danh sách KPI phù hợp với dataset.
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

        is_finance = self._is_finance_dataset(
            df=df,
            dataset_type=dataset_type,
        )

        if is_finance:
            kpis.extend(
                self._generate_finance_kpis(df)
            )
        else:
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

    def _is_finance_dataset(
        self,
        df: pd.DataFrame,
        dataset_type: str,
    ) -> bool:
        """
        Nhận diện dataset tài chính dựa trên loại dataset
        hoặc tên cột.
        """

        normalized_type = (
            dataset_type
            .strip()
            .lower()
        )

        if normalized_type in {
            "finance",
            "financial",
            "banking",
            "transaction",
            "payments",
        }:
            return True

        matched_keywords = 0

        for column in df.columns:
            normalized_column = self._normalize_name(
                str(column)
            )

            tokens = set(
                normalized_column.split("_")
            )

            if tokens & self.FINANCE_KEYWORDS:
                matched_keywords += 1

        return matched_keywords >= 3

    def _generate_finance_kpis(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        """
        KPI dành riêng cho dữ liệu tài chính/giao dịch.
        """

        kpis: list[dict[str, Any]] = []

        transaction_column = self._find_dataframe_column(
            df=df,
            candidates={
                "transaction_id",
                "payment_id",
                "order_id",
                "invoice_id",
            },
        )

        amount_column = self._find_dataframe_column(
            df=df,
            candidates={
                "amount",
                "transaction_amount",
                "payment_value",
                "payment_amount",
                "total_amount",
                "value",
            },
        )

        fee_column = self._find_dataframe_column(
            df=df,
            candidates={
                "transaction_fee",
                "payment_fee",
                "service_fee",
                "fee",
            },
        )

        status_column = self._find_dataframe_column(
            df=df,
            candidates={
                "status",
                "transaction_status",
                "payment_status",
                "order_status",
            },
        )

        risk_column = self._find_dataframe_column(
            df=df,
            candidates={
                "risk_level",
                "risk_category",
                "risk_status",
            },
        )

        if transaction_column:
            transaction_count = self._safe_nunique(
                df,
                transaction_column,
            )
        else:
            transaction_count = int(len(df))

        kpis.append({
            "id": "total_transactions",
            "title": "Total Transactions",
            "value": transaction_count,
            "format": "integer",
            "column": transaction_column,
            "aggregation": "nunique",
            "priority": 110,
        })

        if amount_column:
            total_amount = self._safe_sum(
                df,
                amount_column,
            )

            average_amount = self._safe_mean(
                df,
                amount_column,
            )

            kpis.append({
                "id": "total_transaction_amount",
                "title": "Total Transaction Amount",
                "value": total_amount,
                "format": "currency",
                "column": amount_column,
                "aggregation": "sum",
                "priority": 109,
            })

            kpis.append({
                "id": "average_transaction_value",
                "title": "Average Transaction Value",
                "value": average_amount,
                "format": "currency",
                "column": amount_column,
                "aggregation": "mean",
                "priority": 108,
            })

        if fee_column:
            kpis.append({
                "id": "total_transaction_fee",
                "title": "Total Transaction Fee",
                "value": self._safe_sum(
                    df,
                    fee_column,
                ),
                "format": "currency",
                "column": fee_column,
                "aggregation": "sum",
                "priority": 107,
            })

        if status_column:
            completed_rate = self._calculate_category_rate(
                df=df,
                column_name=status_column,
                accepted_values={
                    "completed",
                    "complete",
                    "success",
                    "successful",
                    "paid",
                    "approved",
                },
            )

            kpis.append({
                "id": "completed_transaction_rate",
                "title": "Completed Rate",
                "value": completed_rate,
                "format": "percentage",
                "column": status_column,
                "aggregation": "rate",
                "priority": 106,
            })

        if risk_column:
            high_risk_count = self._count_category_values(
                df=df,
                column_name=risk_column,
                accepted_values={
                    "high",
                    "high risk",
                    "critical",
                    "very high",
                },
            )

            kpis.append({
                "id": "high_risk_transactions",
                "title": "High-Risk Transactions",
                "value": high_risk_count,
                "format": "integer",
                "column": risk_column,
                "aggregation": "count",
                "priority": 105,
            })

        return kpis

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

        customer_column = self._find_column(
            data_context=data_context,
            keywords={
                "customer_id",
                "customer_unique_id",
                "client_id",
            },
            roles={"identifier"},
        )

        profit_column = self._find_column(
            data_context=data_context,
            keywords={
                "profit",
                "net_profit",
                "gross_profit",
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
                "priority": 95,
            })

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
                "priority": 94,
            })

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
                "priority": 90,
            })

        if revenue_column and order_column:
            revenue = self._safe_sum(
                df,
                revenue_column,
            )

            orders = self._safe_nunique(
                df,
                order_column,
            )

            average_order_value = (
                revenue / orders
                if orders > 0
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
                "aggregation": "average_order_value",
                "priority": 92,
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

        location_column = self._find_column(
            data_context=data_context,
            keywords={
                "customer_city",
                "city",
                "province",
                "state",
            },
            roles={"dimension"},
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

        if location_column:
            kpis.append({
                "id": "covered_locations",
                "title": "Covered Locations",
                "value": self._safe_nunique(
                    df,
                    location_column,
                ),
                "format": "integer",
                "column": location_column,
                "aggregation": "nunique",
                "priority": 80,
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

        product_column = self._find_column(
            data_context=data_context,
            keywords={
                "product_id",
                "sku",
                "item_id",
            },
            roles={"identifier"},
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

        salary_column = self._find_column(
            data_context=data_context,
            keywords={
                "salary",
                "income",
                "wage",
            },
            roles={"measure"},
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

            normalized_name = self._normalize_name(
                column_name
            )

            if normalized_name in self.ADMISSION_SCORE_COLUMNS:
                # Điểm xét tuyển được xử lý riêng theo từng
                # phương thức để tránh trộn nhiều thang điểm.
                continue

            aggregation = self._infer_aggregation(
                column_name=normalized_name,
                default_aggregation=(
                    measure.get("aggregation")
                    or "sum"
                ),
            )
            print(
                "[KPI]",
                "column=",
                column_name,
                "normalized=",
                normalized_name,
                "input_aggregation=",
                measure.get("aggregation"),
                "resolved_aggregation=",
                aggregation,
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



    def _infer_aggregation(
        self,
        column_name: str,
        default_aggregation: str,
    ) -> str:
        """
        Các cột điểm, GPA, CPA, tỷ lệ
        phải dùng mean thay vì sum.
        """

        normalized_name = self._normalize_name(
            column_name
        )

        exact_mean_columns = {
            "gpa",
            "cpa",
            "average_score",
            "final_score",
            "midterm_score",
            "conduct_score",
            "grade_point",
            "admission_score",
            "entrance_score",
            "application_score",
            "admission_points",
            "diem_xet_tuyen",
            "tong_diem_xet_tuyen",
            "điểm_xét_tuyển",
            "tổng_điểm_xét_tuyển",
        }

        if normalized_name in exact_mean_columns:
            return "mean"

        tokens = set(
            normalized_name.split("_")
        )

        mean_tokens = {
            "score",
            "gpa",
            "cpa",
            "grade",
            "mark",
            "point",
            "rating",
            "rate",
            "percentage",
            "percent",
            "diem",
            "điểm",
        }

        if tokens & mean_tokens:
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
            return default_aggregation

        return "sum"
   
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
            "education",
            "student",
            "academic",
            "generic",
        }:
            return []

        kpis: list[dict[str, Any]] = []

        identifiers = data_context.get(
            "identifiers",
            [],
        )

        # Ưu tiên mã sinh viên thực sự.
        for identifier in identifiers:
            column_name = identifier.get("name")

            if (
                not column_name
                or column_name not in df.columns
            ):
                continue

            normalized_name = self._normalize_name(
                column_name
            )

            if (
                normalized_name
                not in self.STUDENT_IDENTIFIER_COLUMNS
            ):
                continue

            kpis.append({
                "id": "total_students",
                "title": "Tổng số sinh viên",
                "value": self._safe_nunique(
                    df,
                    column_name,
                ),
                "format": "integer",
                "column": column_name,
                "aggregation": "nunique",
                "priority": 105,
            })

            return kpis

        # Nếu không có mã sinh viên nhưng có STT,
        # dùng số dòng làm số sinh viên.
        normalized_columns = {
            self._normalize_name(str(column)): str(column)
            for column in df.columns
        }

        row_index_column = next(
            (
                normalized_columns[name]
                for name in self.ROW_INDEX_COLUMNS
                if name in normalized_columns
            ),
            None,
        )

        if row_index_column:
            kpis.append({
                "id": "total_students",
                "title": "Tổng số sinh viên",
                "value": int(len(df)),
                "format": "integer",
                "column": row_index_column,
                "aggregation": "count",
                "priority": 105,
            })

        return kpis

    def _generate_fallback_kpis(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        """
        Fallback vẫn cố tạo KPI hợp lý từ tên cột.
        """

        if self._is_finance_dataset(
            df=df,
            dataset_type="generic",
        ):
            return self._generate_finance_kpis(df)

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

    def _find_dataframe_column(
        self,
        df: pd.DataFrame,
        candidates: set[str],
    ) -> str | None:
        normalized_columns = {
            self._normalize_name(str(column)): str(column)
            for column in df.columns
        }

        for candidate in candidates:
            if candidate in normalized_columns:
                return normalized_columns[candidate]

        for normalized_name, original_name in (
            normalized_columns.items()
        ):
            tokens = set(
                normalized_name.split("_")
            )

            for candidate in candidates:
                candidate_tokens = set(
                    candidate.split("_")
                )

                if candidate_tokens.issubset(tokens):
                    return original_name

        return None

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

            normalized_name = (
                column.get("normalized_name")
                or self._normalize_name(name)
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

    def _calculate_category_rate(
        self,
        df: pd.DataFrame,
        column_name: str,
        accepted_values: set[str],
    ) -> float:
        series = (
            df[column_name]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
        )

        if series.empty:
            return 0.0

        matched = series.isin(
            accepted_values
        ).sum()

        return round(
            float(matched / len(series) * 100),
            2,
        )

    def _count_category_values(
        self,
        df: pd.DataFrame,
        column_name: str,
        accepted_values: set[str],
    ) -> int:
        series = (
            df[column_name]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return int(
            series.isin(
                accepted_values
            ).sum()
        )

    def _safe_sum(
        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> int | float:
        series = pd.to_numeric(
            df[column_name],
            errors="coerce",
        )

        return self._json_number(
            series.sum()
        )

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
        normalized_name = self._normalize_name(
            column_name
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
        normalized_name = self._normalize_name(
            column_name
        )

        return (
            f"{aggregation}_{normalized_name}"
        )


    def _make_title(
        self,
        aggregation: str,
        column_name: str,
    ) -> str:
        normalized = self._normalize_name(
            column_name
        )

        display = self._format_column_name(
            column_name
        )

        if aggregation == "mean":
            if normalized == "cpa":
                return "Điểm trung bình CPA"

            if normalized == "gpa":
                return "Điểm trung bình GPA"

            if normalized in {
                "average_score",
                "final_score",
                "midterm_score",
                "conduct_score",
                "grade_point",
            }:
                return f"{display} trung bình"

            return f"Trung bình {display.lower()}"

        if aggregation == "sum":
            return f"Tổng {display.lower()}"

        if aggregation == "nunique":
            return f"Số lượng {display.lower()}"

        if aggregation == "count":
            return f"Tổng {display.lower()}"

        return display

   
    def _normalize_name(
        self,
        value: str,
    ) -> str:
        return (
            value
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )


    def _format_column_name(
        self,
        column_name: str,
    ) -> str:

        normalized = self._normalize_name(
            column_name
        )

        if normalized in self.DISPLAY_NAME:
            return self.DISPLAY_NAME[
                normalized
            ]

        return (
            column_name
            .replace("_", " ")
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



    def _make_description(
        self,
        aggregation: str,
        column_name: str,
    ) -> str:

        normalized = self._normalize_name(
            column_name
        )

        if normalized in self.DESCRIPTION:
            return self.DESCRIPTION[
                normalized
            ]

        display = self._format_column_name(
            column_name
        )

        if aggregation == "mean":
            return (
                f"Giá trị trung bình của "
                f"{display.lower()}."
            )

        if aggregation == "sum":
            return (
                f"Tổng {display.lower()} "
                f"trong toàn bộ dữ liệu."
            )

        if aggregation == "nunique":
            return (
                f"Số lượng "
                f"{display.lower()} duy nhất."
            )

        return display


    def _safe_score_mean(
        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> int | float:
        series = self._clean_score_series(
            df=df,
            column_name=column_name,
        )

        if series.empty:
            return 0

        return round(
            float(series.mean()),
            2,
        )


    def _clean_score_series(

        self,
        df: pd.DataFrame,
        column_name: str,
    ) -> pd.Series:
        """
        Chuẩn hóa cột điểm bị mất dấu thập phân.

        Ví dụ:
        867  -> 8.67
        761  -> 7.61
        977  -> 9.77

        Các giá trị điểm hợp lệ như 20.34, 25.5
        được giữ nguyên.
        """

        series = pd.to_numeric(
            df[column_name],
            errors="coerce",
        ).dropna()

        def normalize_score(value: float) -> float:
            value = float(value)

            if value > 100:
                return value / 100

            if value > 30:
                return value / 10

            return value

        return series.apply(normalize_score)


    def _find_column(
        self,
        df: pd.DataFrame,
        candidates: set[str],
    ) -> str | None:
        """
        Tìm tên cột thật trong DataFrame dựa trên tên đã chuẩn hóa.
        """

        for column_name in df.columns:
            normalized_name = self._normalize_name(
                str(column_name)
            )

            if normalized_name in candidates:
                return str(column_name)

        return None


    def _generate_admission_score_kpis(
        self,
        df: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        """
        Tạo KPI điểm xét tuyển trung bình theo từng phương thức.

        Không lấy trung bình chung vì các phương thức có thể
        sử dụng thang điểm khác nhau, ví dụ:

        - Điểm thi THPT / học bạ: thang 30
        - ĐGNL ĐHQG: thang khoảng 1.200
        """

        score_column = self._find_column(
            df=df,
            candidates=self.ADMISSION_SCORE_COLUMNS,
        )

        method_column = self._find_column(
            df=df,
            candidates=self.ADMISSION_METHOD_COLUMNS,
        )

        if not score_column or not method_column:
            return []

        working_df = df[
            [
                method_column,
                score_column,
            ]
        ].copy()

        working_df[score_column] = pd.to_numeric(
            working_df[score_column],
            errors="coerce",
        )

        working_df[method_column] = (
            working_df[method_column]
            .astype("string")
            .str.strip()
        )

        working_df = working_df.dropna(
            subset=[
                method_column,
                score_column,
            ]
        )

        if working_df.empty:
            return []

        grouped = (
            working_df.groupby(
                method_column,
                dropna=True,
            )[score_column]
            .agg(
                average="mean",
                count="count",
            )
            .reset_index()
        )

        grouped = grouped.sort_values(
            by="count",
            ascending=False,
        )

        kpis: list[dict[str, Any]] = []

        for _, row in grouped.iterrows():
            method_name = str(
                row[method_column]
            ).strip()

            average_score = round(
                float(row["average"]),
                2,
            )

            short_method_name = (
                self._shorten_admission_method(
                    method_name
                )
            )

            kpis.append(
                {
                    "title": (
                        f"Điểm TB {short_method_name}"
                    ),
                    "value": average_score,
                    "aggregation": "mean",
                    "column": score_column,
                    "group_by": method_column,
                    "group_value": method_name,
                    "reason": (
                        "Điểm xét tuyển được tính riêng "
                        "theo từng phương thức do sử dụng "
                        "các thang điểm khác nhau."
                    ),
                }
            )

        return kpis



    def _shorten_admission_method(
     
        self,
        method_name: str,
    ) -> str:
        """
        Rút gọn tên phương thức để KPI không quá dài.
        """

        normalized_name = (
            method_name
            .strip()
            .lower()
        )

        if "đgnl" in normalized_name:
            return "ĐGNL"

        if "đánh giá năng lực" in normalized_name:
            return "ĐGNL"

        if "thpt" in normalized_name:
            return "THPT"

        if "học bạ" in normalized_name:
            return "học bạ"

        if "tuyển thẳng" in normalized_name:
            return "tuyển thẳng"

        return method_name