import pandas as pd


class ChartGenerator:

    def generate(self, df: pd.DataFrame):

        charts = []

        # ==========================
        # Line Chart
        # ==========================
        line_chart = self.generate_line_chart(df)

        if line_chart:
            charts.append(line_chart)

        # ==========================
        # Bar Chart
        # ==========================
        bar_chart = self.generate_bar_chart(df)

        if bar_chart:
            charts.append(bar_chart)

        # ==========================
        # Pie Chart
        # ==========================
        pie_chart = self.generate_pie_chart(df)

        if pie_chart:
            charts.append(pie_chart)



        return charts

    # ==========================
    # Detect datetime column
    # ==========================
    def detect_datetime_column(self, df):

        for col in df.columns:


            # Column đã là datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col



            # Thử convert string -> datetime
            try:

                converted = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )


                valid_ratio = converted.notna().mean()


                # 80% dữ liệu convert được
                if valid_ratio > 0.8:
                    return col

            except:
                pass



        return None


    # ==========================
    # Smart Line Chart Generator
    # ==========================
    def generate_line_chart(self, df):


        date_col = self.detect_datetime_column(df)


        if date_col is None:
            return None



        numeric_cols = df.select_dtypes(
            include="number"
        ).columns



        if len(numeric_cols) == 0:
            return None



        value_col = numeric_cols[0]



        # Convert datetime để sort
        temp_df = df.copy()


        temp_df[date_col] = pd.to_datetime(
            temp_df[date_col],
            errors="coerce"
        )


        temp_df = (
            temp_df[[date_col, value_col]]
            .dropna()
            .sort_values(date_col)
            .head(100)
        )


        return {

            "type": "line",

            "title": f"{value_col} Trend Over Time",

            "x_axis": date_col,

            "y_axis": value_col,


            "data": temp_df.to_dict(
                orient="records"
            )

        }



    # ==========================
    # Smart Bar Chart Generator
    # ==========================
    def generate_bar_chart(self, df: pd.DataFrame):


        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns


        selected_column = None



        for column in categorical_columns:


            unique = df[column].nunique()



            # Chỉ chọn category vừa phải
            if unique < 2 or unique > 30:
                continue



            # Bỏ qua ID
            if column.lower().endswith("_id"):
                continue



            selected_column = column

            break



        if selected_column is None:
            return None



        top = (
            df[selected_column]
            .value_counts()
            .head(10)
        )



        return {


            "type": "bar",


            "title": f"Top {selected_column}",


            "x": top.index.tolist(),


            "y": top.values.tolist()

        }




    # ==========================
    # Smart Pie Chart Generator
    # ==========================
    def generate_pie_chart(self, df: pd.DataFrame):


        categorical_columns = df.select_dtypes(
            include=["object", "category"]
        ).columns



        selected_column = None



        for column in categorical_columns:


            unique = df[column].nunique()



            # Pie đẹp khi ít nhóm
            if unique < 2 or unique > 8:
                continue



            # Không dùng ID
            if column.lower().endswith("_id"):
                continue



            selected_column = column

            break



        if selected_column is None:
            return None



        counts = (
            df[selected_column]
            .value_counts()
        )



        return {


            "type": "pie",


            "title": f"{selected_column} Distribution",


            "labels": counts.index.tolist(),


            "values": counts.values.tolist()

        }