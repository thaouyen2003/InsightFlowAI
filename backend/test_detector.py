from app.services.schema.detector import SemanticDetector


columns = [

    "customer_id",

    "payment_value",

    "order_purchase_timestamp",

    "customer_city",

    "product_category_name",

    "unknown_column"

]


for column in columns:

    semantic = SemanticDetector.detect(column)

    print(f"{column:35} -> {semantic}")