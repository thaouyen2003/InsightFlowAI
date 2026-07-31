import pandas as pd


class KPIGenerator:

    def generate(self, df):

        kpis = [

            {
                "title": "Rows",
                "value": len(df)
            },

            {
                "title": "Columns",
                "value": len(df.columns)
            }

        ]

        for column in df.columns:

            # Chỉ xử lý cột số
            if not pd.api.types.is_numeric_dtype(df[column]):
                continue

            total = df[column].sum()

            if pd.api.types.is_integer_dtype(df[column]):
                total = int(total)
            else:
                total = float(total)

            kpis.append({

                "title": f"Total {column}",

                "value": total

            })

        return kpis