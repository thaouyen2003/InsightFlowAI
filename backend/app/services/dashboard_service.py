import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]

payments = pd.read_csv(BASE/"database"/"olist_order_payments_dataset.csv")

orders = pd.read_csv(BASE/"database"/"olist_orders_dataset.csv")


def get_dashboard():

    revenue = payments.payment_value.sum()

    avg = payments.payment_value.mean()

    payment_chart = (
        payments.groupby("payment_type")["payment_value"]
        .sum()
        .reset_index()
        .to_dict("records")
    )

    return {

        "kpi":{

            "revenue":round(revenue,2),

            "orders":len(orders),

            "customers":orders.customer_id.nunique(),

            "avg_order":round(avg,2)

        },

        "payment_chart":payment_chart

    }