import pandas as pd


class ChartRecommender:


    def recommend(self, df):

        recommendations = []


        # Detect datetime
        date_columns = self.detect_datetime(df)


        # Detect numeric
        numeric_columns = (
            df.select_dtypes(
                include="number"
            )
            .columns
        )


        # ==========================
        # Time Series Recommendation
        # ==========================

        if (
            len(date_columns) > 0
            and len(numeric_columns) > 0
        ):

            recommendations.append({

                "chart": "line",

                "reason":
                "Detected datetime column and numeric metric. Suitable for trend analysis."

            })



        # ==========================
        # Category Comparison
        # ==========================

        categorical_columns = (
            df.select_dtypes(
                include=[
                    "object",
                    "category"
                ]
            )
            .columns
        )


        if len(categorical_columns) > 0:


            recommendations.append({

                "chart": "bar",

                "reason":
                "Detected categorical data. Suitable for comparison."

            })



        # ==========================
        # Distribution
        # ==========================

        for col in categorical_columns:

            unique = df[col].nunique()


            if 2 <= unique <= 8:

                recommendations.append({

                    "chart":"pie",

                    "reason":
                    "Small number of categories detected. Suitable for distribution."

                })

                break



        return recommendations



    def detect_datetime(self, df):

        result=[]


        for col in df.columns:


            try:

                converted = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )


                if converted.notna().mean() > 0.8:

                    result.append(col)


            except:
                pass


        return result