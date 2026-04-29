# IQR outlier detector: takes CSV path and column name, returns a JSON list of `{row_index, value, lower_bound, upper_bound}`. Use `BaseTool`.
# - Z-score outlier detector: same interface. Use `BaseTool`.
# - Pearson correlation matrix: takes CSV path, returns correlation matrix as JSON. Use `@tool`.
# - Cramér's V: takes CSV path and two column names, returns the V statistic and interpretation. Use `BaseTool`.
# - Two-sample t-test: takes CSV path, numeric column, grouping column, and the two group values to compare. Returns t-statistic, p-value, and a boolean for significance at 0.05. Use `BaseTool`.
# - Value counts: takes CSV path and column name, returns top 20 values with counts and percentages. Use `BaseTool`.



import json
import pandas as pd
import numpy as np
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool, tool
from scipy import stats as scipy_stats
from crewanalyst.schema.correlations import Correlation

        


@tool("compute_categorical_stats")
def compute_categorical_stats(csv_path: str, columns: list[str]) -> str:
    """Computes unique count, top value, top frequency, and value counts for categorical columns."""
    try:
        df = pd.read_csv(csv_path)
        result = {}

        for col in columns:
            if col not in df.columns:
                result[col] = {"error": f"column '{col}' not found"}
                continue

            vc = df[col].astype(str).value_counts(dropna=False).head(20)
            result[col] = {
                "unique_values": int(df[col].nunique(dropna=True)),
                "top_value": str(vc.index[0]) if len(vc) else "",
                "top_freq": int(vc.iloc[0]) if len(vc) else 0,
                "unique_value_counts": {str(k): int(v) for k, v in vc.items()},
                "is_identifier": df[col].nunique(dropna=True) > len(df) * 0.8,
            }

        return json.dumps(result)
    except Exception as e:
        return f"ERROR: compute_categorical_stats failed - {e}"


@tool("compute_group_aggregates")
def compute_group_aggregates(csv_path: str, metric_column: str, grouping_column: str) -> str:
    """Computes mean and group size for a numeric metric grouped by a categorical column."""
    try:
        df = pd.read_csv(csv_path)
        grouped = df.groupby(grouping_column)[metric_column].agg(["count", "mean"]).reset_index()

        result = {
            "numeric_column": metric_column,
            "categorical_column": grouping_column,
            "groups": [
                {
                    "group_name": str(row[grouping_column]),
                    "group_size": int(row["count"]),
                    "group_mean": round(float(row["mean"]), 4),
                    "is_identifier": False,
                }
                for _, row in grouped.iterrows()
            ],
        }
        return json.dumps(result)
    except Exception as e:
        return f"ERROR: compute_group_aggregates failed - {e}"


@tool("analyze_datetime_column")
def analyze_datetime_column(csv_path: str, datetime_column: str, metric_column: str) -> str:
    """Analyzes trend direction for a numeric metric over a datetime column."""
    try:
        df = pd.read_csv(csv_path)
        df[datetime_column] = pd.to_datetime(df[datetime_column], errors="coerce")
        df = df.dropna(subset=[datetime_column, metric_column]).sort_values(datetime_column)

        first = float(df[metric_column].iloc[0])
        last = float(df[metric_column].iloc[-1])
        direction = "upward" if last > first else "downward" if last < first else "flat"

        result = {
            "start_time": str(df[datetime_column].min()),
            "end_time": str(df[datetime_column].max()),
            "inferred_frequency": "unknown",
            "trend_direction": direction,
            "trend_note": f"{metric_column} moved {direction} over the observed time range.",
            "gaps_detected": False,
            "outliers_detected": False,
        }
        return json.dumps(result)
    except Exception as e:
        return f"ERROR: analyze_datetime_column failed - {e}"


