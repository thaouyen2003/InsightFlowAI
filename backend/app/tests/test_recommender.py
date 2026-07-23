import pandas as pd

from app.services.chart_recommender import ChartRecommender



df = pd.read_csv(
    "../database/olist_order_payments_dataset.csv"
)



recommender = ChartRecommender()


result = recommender.recommend(df)



print(result)