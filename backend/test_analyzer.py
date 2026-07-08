import pandas as pd

from app.services.schema.analyzer import SchemaAnalyzer

# Đọc dữ liệu
df = pd.read_csv("../database/olist_customers_dataset.csv")

# Khởi tạo Analyzer
analyzer = SchemaAnalyzer()

# Phân tích
result = analyzer.analyze(df)

# In kết quả dạng dict
print(result.to_dict())