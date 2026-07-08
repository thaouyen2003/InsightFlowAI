import pandas as pd


def analyze_profile(df):

    columns = []

    for col in df.columns:

        series = df[col]

        profile = {
            "name": col,
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique())
        }


        # categorical
        if series.dtype == "object":

            profile["type"] = "categorical"

            profile["top_values"] = (
                series
                .value_counts()
                .head(5)
                .to_dict()
            )


        # numeric
        elif pd.api.types.is_numeric_dtype(series):

            profile["type"] = "numeric"

            profile["min"] = float(series.min())
            profile["max"] = float(series.max())
            profile["mean"] = float(series.mean())


        columns.append(profile)


    return {
        "columns": columns
    }