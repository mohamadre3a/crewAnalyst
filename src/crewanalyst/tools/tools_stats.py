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

# from crewanalyst.schema.stats import NumericColumnStats

class IQROutlierInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column_name: str = Field(description="Name of the numeric column to analyze")
    
    
class IQROutlierTool(BaseTool):
    name: str = "detect_outliers_iqr"
    description: str = (
        "Detects outliers in a numeric column using the IQR method "
        "(values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR). "
        "Returns row indices, values, and bounds for each outlier found."
    )
    args_schema: Type[BaseModel] = IQROutlierInput
    
    def _run(self, args: IQROutlierInput) -> str:
        try:
            df = pd.read_csv(args.csv_path)
            if args.column_name not in df.columns:
                return f"ERROR: Column '{args.column_name}' not found in CSV."
            if not pd.api.types.is_numeric_dtype(df[args.column_name]):
                return f"ERROR: Column '{args.column_name}' is not numeric."
            
            col_data = df[args.column_name].dropna()
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[
                (df[args.column_name] < lower_bound) | 
                (df[args.column_name] > upper_bound)
            ][args.column_name]
            
            result = [
                {
                    "row_index": idx,
                    "value": val,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound
                }
                for idx, val in outliers.items()
            ]
            return json.dumps(result, default=str)
        except Exception as e:
            return f"ERROR: detect_outliers_iqr failed — {e}"
        
        
class ZScoreOutlierInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column: str = Field(description="Numeric column to check for outliers")
    threshold: float = Field(default=3.0, description="Z-score threshold — values above this are flagged. Default is 3.0.")

class ZScoreOutlierTool(BaseTool):
    name: str = "detect_outliers_zscore"
    description: str = (
        "Detects outliers in a numeric column using Z-score method. "
        "Values whose absolute Z-score exceeds the threshold (default 3.0) "
        "are flagged. Use alongside IQR — agreement between both methods "
        "indicates a stronger anomaly."
    )
    args_schema: Type[BaseModel] = ZScoreOutlierInput

    def _run(self, csv_path: str, column: str, threshold: float = 3.0) -> str:
        try:
            df = pd.read_csv(csv_path)
            if column not in df.columns:
                return f"ERROR: column '{column}' not found in CSV"

            s = df[column].dropna()
            z_scores = np.abs((s - s.mean()) / s.std())
            outlier_indices = s.index[z_scores > threshold].tolist()

            result = {
                "column": column,
                "method": "zscore",
                "threshold": threshold,
                "outlier_count": len(outlier_indices),
                "outliers": [
                    {
                        "row_index": int(idx),
                        "value": float(df.loc[idx, column]),
                        "zscore": round(float(z_scores[s.index.get_loc(idx)]), 4),
                    }
                    for idx in outlier_indices
                ],
            }
            return json.dumps(result)
        except Exception as e:
            return f"ERROR: detect_outliers_zscore failed — {e}"


class RareCategoryInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column: str = Field(description="Categorical column to check for rare values")
    threshold_pct: float = Field(default=1.0, description="Values appearing in less than this percentage of rows are flagged as rare")

class RareCategoryTool(BaseTool):
    name: str = "detect_rare_categories"
    description: str = (
        "Flags categorical values that appear in fewer than threshold_pct "
        "percent of rows. Rare categories can indicate typos, data entry "
        "errors, or genuinely unusual cases worth investigating."
    )
    args_schema: Type[BaseModel] = RareCategoryInput

    def _run(self, csv_path: str, column: str, threshold_pct: float = 1.0) -> str:
        try:
            df = pd.read_csv(csv_path)
            if column not in df.columns:
                return f"ERROR: column '{column}' not found in CSV"

            total = len(df)
            vc = df[column].value_counts()
            rare = vc[vc / total * 100 < threshold_pct]

            result = {
                "column": column,
                "threshold_pct": threshold_pct,
                "rare_count": len(rare),
                "rare_values": [
                    {
                        "value": str(val),
                        "count": int(count),
                        "pct": round(count / total * 100, 4),
                    }
                    for val, count in rare.items()
                ],
            }
            return json.dumps(result)
        except Exception as e:
            return f"ERROR: detect_rare_categories failed — {e}"



class TTestInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    metric_column: str = Field(description="Numeric column to compare between groups")
    grouping_column: str = Field(description="Categorical column that defines the two groups")
    group_a: str = Field(description="First group value as a string")
    group_b: str = Field(description="Second group value as a string")

class TTestTool(BaseTool):
    name: str = "run_ttest"
    description: str = (
        "Runs an independent samples t-test between two groups defined by a "
        "categorical column. Returns t-statistic, p-value, and whether the "
        "difference is statistically significant at the 0.05 level. "
        "Use after compute_group_aggregates to determine if observed differences are real."
    )
    args_schema: Type[BaseModel] = TTestInput

    def _run(
        self,
        csv_path: str,
        metric_column: str,
        grouping_column: str,
        group_a: str,
        group_b: str,
    ) -> str:
        try:
            df = pd.read_csv(csv_path)
            for col in [metric_column, grouping_column]:
                if col not in df.columns:
                    return f"ERROR: column '{col}' not found in CSV"

            a_vals = df[df[grouping_column].astype(str) == group_a][metric_column].dropna()
            b_vals = df[df[grouping_column].astype(str) == group_b][metric_column].dropna()

            if len(a_vals) < 2 or len(b_vals) < 2:
                return "ERROR: one or both groups have fewer than 2 observations — t-test cannot run"

            t_stat, p_value = scipy_stats.ttest_ind(a_vals, b_vals, equal_var=False)

            result = {
                "metric_column": metric_column,
                "grouping_column": grouping_column,
                "group_a": group_a,
                "group_b": group_b,
                "group_a_mean": round(float(a_vals.mean()), 4),
                "group_b_mean": round(float(b_vals.mean()), 4),
                "t_statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 6),
                "significant_at_005": bool(p_value < 0.05),
            }
            return json.dumps(result)
        except Exception as e:
            return f"ERROR: run_ttest failed — {e}"


class CramersVInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column_a: str = Field(description="First categorical column")
    column_b: str = Field(description="Second categorical column")

class CramersVTool(BaseTool):
    name: str = "compute_cramers_v"
    description: str = (
        "Computes Cramér's V association statistic between two categorical columns. "
        "V ranges from 0 (no association) to 1 (perfect association). "
        "Use for categorical-categorical pairs where Pearson is not applicable."
    )
    args_schema: Type[BaseModel] = CramersVInput

    def _run(self, csv_path: str, column_a: str, column_b: str) -> str:
        try:
            df = pd.read_csv(csv_path)
            for col in [column_a, column_b]:
                if col not in df.columns:
                    return f"ERROR: column '{col}' not found in CSV"

            contingency = pd.crosstab(df[column_a], df[column_b])
            chi2, p_value, _, _ = scipy_stats.chi2_contingency(contingency)
            n = contingency.sum().sum()
            min_dim = min(contingency.shape) - 1
            v = float(np.sqrt(chi2 / (n * min_dim))) if min_dim > 0 else 0.0

            if v > 0.5:
                strength = "strong"
            elif v > 0.3:
                strength = "moderate"
            else:
                strength = "weak"

            result = Correlation(
                column_a=column_a,
                column_b=column_b,
                coefficient=round(v, 4),
                method="cramers_v",
                direction="none",
                strength=strength,
                plain_english=(
                    f"{column_a} and {column_b} have a {strength} association "
                    f"(Cramér's V = {round(v, 4)}, p = {round(float(p_value), 6)})."
                ),
                is_redundant=v > 0.95,
            ).model_dump()

            return json.dumps(result)
        except Exception as e:
            return f"ERROR: compute_cramers_v failed — {e}"


iqr_outlier_tool = IQROutlierTool()
zscore_outlier_tool = ZScoreOutlierTool()
rare_category_tool = RareCategoryTool()
ttest_tool = TTestTool()
cramers_v_tool = CramersVTool()