import pandas as pd

import sys
import os


from app.services.dashboard.chart_generator import ChartGenerator
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../.."
        )
    )
)



# Load dataset
df = pd.read_csv(
    "../database/olist_orders_dataset.csv"
)


print("====================")
print("Dataset:")
print(df.head())
print("====================")



# Convert datetime column
if "order_purchase_timestamp" in df.columns:

    df["order_purchase_timestamp"] = pd.to_datetime(
        df["order_purchase_timestamp"]
    )



# Generate charts
generator = ChartGenerator()


charts = generator.generate(df)



print("\n====================")
print("GENERATED CHARTS")
print("====================")


for chart in charts:

    print("\nChart Type:")
    print(chart["type"])


    print("Title:")
    print(chart["title"])


    print(chart)
