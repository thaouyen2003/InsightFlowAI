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

    # Lấy dữ liệu từ file upload

    def load_dataframe(self, filename: str):
        filepath = DATA_DIR / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Dataset not found: {filepath}")

        extension = filepath.suffix.lower()

        if extension == ".csv":
            return pd.read_csv(filepath)
        elif extension in [".xlsx", ".xls"]:
            return pd.read_excel(filepath)
        elif extension == ".json":
            return pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {extension}")


data_service = DataService()