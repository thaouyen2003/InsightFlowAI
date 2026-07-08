import pandas as pd

from app.services.schema.profiler import ColumnProfiler


df = pd.read_csv("../database/olist_customers_dataset.csv")

profiler = ColumnProfiler()

profile = profiler.profile(
    df,
    "customer_id"
)

print(profile)