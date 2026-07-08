from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

DATA_DIR = BASE_DIR / "database"


class DataService:

    def __init__(self):
        self.orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
        self.order_items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
        self.payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")
        self.customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")

    def get_kpi(self):

        revenue = round(self.payments["payment_value"].sum(), 2)

        orders = self.orders["order_id"].nunique()

        customers = self.customers["customer_unique_id"].nunique()

        avg_order = round(revenue / orders, 2)

        return {
            "revenue": revenue,
            "orders": orders,
            "customers": customers,
            "avg_order": avg_order
        }


data_service = DataService()