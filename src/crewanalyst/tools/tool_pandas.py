import json
import pandas as pd
import numpy as np
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool, tool

from crewanalyst.schema.stats import NumericColumnStats


@tool("inspect_csv")
def inspect_csv(csv_path: str) -> str:
    """
    Loads a CSV file and returns its shape, column names, dtypes, and a
    10-row sample (first 5 and last 5 rows). Use this as the very first
    step before any other analysis.
    """
    try:
        df = pd.read_csv(csv_path)
        result = {
            "row_count": int(df.shape[0]),
            "column_count": int(df.shape[1]),
            "columns": [
                {"name": col, "dtype": str(df[col].dtype)}
                for col in df.columns
            ],
            "sample_head": df.head(5).to_dict(orient="records"),
            "sample_tail": df.tail(5).to_dict(orient="records"),
        }
        return json.dumps(result, default=str)
    except Exception as e:
        return f"ERROR: inspect_csv failed — {e}"


@tool("get_null_report")
def get_null_report(csv_path: str) -> str:
    """
    Returns null counts and null percentages for every column in the CSV.
    Use this to assess data quality before profiling.
    """
    try:
        df = pd.read_csv(csv_path)
        total = len(df)
        result = [
            {
                "column": col,
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().sum() / total * 100, 2),
            }
            for col in df.columns
        ]
        return json.dumps(result)
    except Exception as e:
        return f"ERROR: get_null_report failed — {e}"


@tool("get_pearson_correlation_matrix")
def get_pearson_correlation_matrix(csv_path: str) -> str:
    """
    Computes the Pearson correlation matrix for all numeric columns in the
    CSV. Returns a JSON object where keys are column names and values are
    dicts of correlations with every other numeric column.
    """
    try:
        df = pd.read_csv(csv_path)
        numeric_df = df.select_dtypes(include="number")
        if numeric_df.shape[1] < 2:
            return "ERROR: fewer than 2 numeric columns — correlation matrix cannot be computed"
        corr = numeric_df.corr(method="pearson")
        return corr.to_json()
    except Exception as e:
        return f"ERROR: get_pearson_correlation_matrix failed — {e}"
    
    
class DescriptiveStatsInput(BaseModel):
    
    csv_path: str = Field(description="Absolute path to the CSV file")
    columns: list[str] = Field(description="List of numeric column names to compute stats for")


class DescriptiveStatsTool(BaseTool):
    name: str =  "get_descriptive_stats"
    description: str = "Computes descriptive statistics (mean, median, std, min, max) for specified numeric columns in a CSV file."
    
    args_schema: Type[BaseModel] = DescriptiveStatsInput

    def _run(self, csv_path: str, columns: list[str]) -> str:
        try:
            df = pd.read_csv(csv_path)
            missing = [c for c in columns if c not in df.columns]
            if missing:
                return f"ERROR: columns not found in CSV — {missing}"

            results = []
            for col in columns:
                s = df[col].dropna()
                results.append(
                    NumericColumnStats(
                        column=col,
                        mean=round(float(s.mean()), 4),
                        median=round(float(s.median()), 4),
                        std=round(float(s.std()), 4),
                        skewness=round(float(s.skew()), 4),
                        kurtosis=round(float(s.kurt()), 4),
                        min=round(float(s.min()), 4),
                        max=round(float(s.max()), 4),
                        p25=round(float(s.quantile(0.25)), 4),
                        p75=round(float(s.quantile(0.75)), 4),
                    ).model_dump()
                )
            return json.dumps(results)
        except Exception as e:
            return f"ERROR: compute_descriptive_stats failed — {e}"
        
        
        
descriptive_stats_tool = DescriptiveStatsTool()