
import json
import base64
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool, tool

sns.set_theme(style="whitegrid", palette="muted")
CHARTS_DIR = Path("outputs/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

def _save_and_return(fig: plt.Figure, output_path: str) -> str:
    """Saves figure, closes it, returns the path string."""
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path



class HistogramInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column: str = Field(description="Numeric column to plot")
    output_filename: str = Field(description="Filename for the output PNG e.g. 'revenue_distribution.png'")

class HistogramTool(BaseTool):
    name: str = "generate_histogram"
    description: str = (
        "Generates a histogram with a KDE curve for a numeric column. "
        "Use to show distribution shape, skewness, and spread. "
        "Best for columns flagged as skewed or with interesting kurtosis."
    )
    args_schema: Type[BaseModel] = HistogramInput

    def _run(self, csv_path: str, column: str, output_filename: str) -> str:
        try:
            df = pd.read_csv(csv_path)
            if column not in df.columns:
                return f"ERROR: column '{column}' not found in CSV"

            output_path = str(CHARTS_DIR / output_filename)
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.histplot(df[column].dropna(), kde=True, ax=ax, color="#4C72B0")
            ax.set_title(f"Distribution of {column}", fontsize=13, fontweight="bold")
            ax.set_xlabel(column)
            ax.set_ylabel("Count")
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_histogram failed — {e}"


class BoxplotInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    metric_column: str = Field(description="Numeric column to plot on y-axis")
    grouping_column: str = Field(description="Categorical column to group by on x-axis")
    output_filename: str = Field(description="Filename for the output PNG")

class BoxplotTool(BaseTool):
    name: str = "generate_boxplot"
    description: str = (
        "Generates a grouped box plot showing distribution of a numeric column "
        "across categories. Use when group comparisons show meaningful differences "
        "or when you want to visualize spread and outliers per group."
    )
    args_schema: Type[BaseModel] = BoxplotInput

    def _run(
        self,
        csv_path: str,
        metric_column: str,
        grouping_column: str,
        output_filename: str,
    ) -> str:
        try:
            df = pd.read_csv(csv_path)
            for col in [metric_column, grouping_column]:
                if col not in df.columns:
                    return f"ERROR: column '{col}' not found in CSV"

            output_path = str(CHARTS_DIR / output_filename)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(data=df, x=grouping_column, y=metric_column, ax=ax, palette="muted")
            ax.set_title(f"{metric_column} by {grouping_column}", fontsize=13, fontweight="bold")
            ax.set_xlabel(grouping_column)
            ax.set_ylabel(metric_column)
            plt.xticks(rotation=30, ha="right")
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_boxplot failed — {e}"


class TimeSeriesInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    datetime_column: str = Field(description="Datetime column for the x-axis")
    metric_column: str = Field(description="Numeric column to plot on y-axis")
    grouping_column: str | None = Field(default=None, description="Optional categorical column to split into multiple lines")
    output_filename: str = Field(description="Filename for the output PNG")

class TimeSeriesTool(BaseTool):
    name: str = "generate_time_series_chart"
    description: str = (
        "Generates a line chart of a numeric metric over time. "
        "Optionally splits into multiple lines by a categorical column. "
        "Only use when a datetime role column exists in the data profile."
    )
    args_schema: Type[BaseModel] = TimeSeriesInput

    def _run(
        self,
        csv_path: str,
        datetime_column: str,
        metric_column: str,
        output_filename: str,
        grouping_column: str | None = None,
    ) -> str:
        try:
            df = pd.read_csv(csv_path, parse_dates=[datetime_column])
            for col in [datetime_column, metric_column]:
                if col not in df.columns:
                    return f"ERROR: column '{col}' not found in CSV"

            df = df.sort_values(datetime_column)
            output_path = str(CHARTS_DIR / output_filename)
            fig, ax = plt.subplots(figsize=(11, 5))

            if grouping_column and grouping_column in df.columns:
                for group, gdf in df.groupby(grouping_column):
                    ax.plot(gdf[datetime_column], gdf[metric_column], label=str(group), linewidth=1.8)
                ax.legend(title=grouping_column, bbox_to_anchor=(1.01, 1), loc="upper left")
            else:
                ax.plot(df[datetime_column], df[metric_column], color="#4C72B0", linewidth=1.8)

            ax.set_title(f"{metric_column} over Time", fontsize=13, fontweight="bold")
            ax.set_xlabel(datetime_column)
            ax.set_ylabel(metric_column)
            plt.xticks(rotation=30, ha="right")
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_time_series_chart failed — {e}"


class CorrelationHeatmapInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    output_filename: str = Field(description="Filename for the output PNG")

class CorrelationHeatmapTool(BaseTool):
    name: str = "generate_correlation_heatmap"
    description: str = (
        "Generates a Pearson correlation heatmap for all numeric columns. "
        "Use when the correlation analysis found several meaningful relationships "
        "worth showing together in one view."
    )
    args_schema: Type[BaseModel] = CorrelationHeatmapInput

    def _run(self, csv_path: str, output_filename: str) -> str:
        try:
            df = pd.read_csv(csv_path)
            numeric_df = df.select_dtypes(include="number")
            if numeric_df.shape[1] < 2:
                return "ERROR: fewer than 2 numeric columns — heatmap cannot be generated"

            output_path = str(CHARTS_DIR / output_filename)
            corr = numeric_df.corr()
            fig, ax = plt.subplots(figsize=(max(6, len(corr) * 1.2), max(5, len(corr) * 1.0)))
            sns.heatmap(
                corr,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                center=0,
                square=True,
                linewidths=0.5,
                ax=ax,
            )
            ax.set_title("Pearson Correlation Matrix", fontsize=13, fontweight="bold")
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_correlation_heatmap failed — {e}"


class BarChartInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column: str = Field(description="Categorical column to plot value counts for")
    top_n: int = Field(default=15, description="Show only the top N categories")
    output_filename: str = Field(description="Filename for the output PNG")

class BarChartTool(BaseTool):
    name: str = "generate_bar_chart"
    description: str = (
        "Generates a horizontal bar chart showing the top N most frequent "
        "values in a categorical column. Use to visualize category distributions "
        "or when a categorical column has high entropy or dominant values."
    )
    args_schema: Type[BaseModel] = BarChartInput

    def _run(self, csv_path: str, column: str, output_filename: str, top_n: int = 15) -> str:
        try:
            df = pd.read_csv(csv_path)
            if column not in df.columns:
                return f"ERROR: column '{column}' not found in CSV"

            output_path = str(CHARTS_DIR / output_filename)
            vc = df[column].value_counts().head(top_n)

            fig, ax = plt.subplots(figsize=(9, max(4, top_n * 0.4)))
            vc.sort_values().plot(kind="barh", ax=ax, color="#4C72B0")
            ax.set_title(f"Top {top_n} values — {column}", fontsize=13, fontweight="bold")
            ax.set_xlabel("Count")
            ax.set_ylabel(column)
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_bar_chart failed — {e}"


class ScatterPlotInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    x_column: str = Field(description="Numeric column for the x-axis")
    y_column: str = Field(description="Numeric column for the y-axis")
    color_column: str | None = Field(default=None, description="Optional categorical column to color points by")
    output_filename: str = Field(description="Filename for the output PNG")

class ScatterPlotTool(BaseTool):
    name: str = "generate_scatter_plot"
    description: str = (
        "Generates a scatter plot for two numeric columns. Optionally colors "
        "points by a categorical column. Use to visualize strong correlations "
        "found by the correlation analyst."
    )
    args_schema: Type[BaseModel] = ScatterPlotInput

    def _run(
        self,
        csv_path: str,
        x_column: str,
        y_column: str,
        output_filename: str,
        color_column: str | None = None,
    ) -> str:
        try:
            df = pd.read_csv(csv_path)
            for col in [x_column, y_column]:
                if col not in df.columns:
                    return f"ERROR: column '{col}' not found in CSV"

            output_path = str(CHARTS_DIR / output_filename)
            fig, ax = plt.subplots(figsize=(8, 6))

            if color_column and color_column in df.columns:
                groups = df[color_column].unique()
                palette = sns.color_palette("muted", len(groups))
                for i, group in enumerate(groups):
                    gdf = df[df[color_column] == group]
                    ax.scatter(gdf[x_column], gdf[y_column], label=str(group), alpha=0.6, color=palette[i], s=30)
                ax.legend(title=color_column, bbox_to_anchor=(1.01, 1), loc="upper left")
            else:
                ax.scatter(df[x_column], df[y_column], alpha=0.5, color="#4C72B0", s=30)

            ax.set_title(f"{x_column} vs {y_column}", fontsize=13, fontweight="bold")
            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_scatter_plot failed — {e}"


class AnomalyHighlightInput(BaseModel):
    csv_path: str = Field(description="Absolute path to the CSV file")
    column: str = Field(description="Numeric column to plot with anomalies highlighted")
    anomaly_indices: list[int] = Field(description="Row indices of anomalous points to highlight in red")
    output_filename: str = Field(description="Filename for the output PNG")

class AnomalyHighlightTool(BaseTool):
    name: str = "generate_anomaly_highlight_chart"
    description: str = (
        "Generates a scatter plot of a numeric column (as an index plot) with "
        "anomalous rows highlighted in red. Use when high severity anomalies "
        "were found to make them visually obvious in the report."
    )
    args_schema: Type[BaseModel] = AnomalyHighlightInput

    def _run(
        self,
        csv_path: str,
        column: str,
        anomaly_indices: list[int],
        output_filename: str,
    ) -> str:
        try:
            df = pd.read_csv(csv_path)
            if column not in df.columns:
                return f"ERROR: column '{column}' not found in CSV"

            output_path = str(CHARTS_DIR / output_filename)
            fig, ax = plt.subplots(figsize=(11, 5))

            normal_mask = ~df.index.isin(anomaly_indices)
            ax.scatter(df.index[normal_mask], df.loc[normal_mask, column], color="#4C72B0", alpha=0.5, s=15, label="Normal")
            ax.scatter(anomaly_indices, df.loc[anomaly_indices, column], color="#C44E52", s=60, zorder=5, label="Anomaly")

            ax.set_title(f"Anomalies in {column}", fontsize=13, fontweight="bold")
            ax.set_xlabel("Row index")
            ax.set_ylabel(column)
            ax.legend()
            return _save_and_return(fig, output_path)
        except Exception as e:
            return f"ERROR: generate_anomaly_highlight_chart failed — {e}"



@tool("convert_charts_to_base64")
def convert_charts_to_base64(file_paths_json: str) -> str:
    """
    Takes a JSON array of chart file paths and returns a JSON object
    mapping each path to its base64-encoded PNG string. The reporter
    agent uses these strings to embed charts directly into the HTML report.
    Pass a JSON array string like: '["outputs/charts/a.png", "outputs/charts/b.png"]'
    """
    try:
        paths = json.loads(file_paths_json)
        result = {}
        for path in paths:
            with open(path, "rb") as f:
                result[path] = base64.b64encode(f.read()).decode("utf-8")
        return json.dumps(result)
    except Exception as e:
        return f"ERROR: convert_charts_to_base64 failed — {e}"



histogram_tool = HistogramTool()
boxplot_tool = BoxplotTool()
time_series_tool = TimeSeriesTool()
correlation_heatmap_tool = CorrelationHeatmapTool()
bar_chart_tool = BarChartTool()
scatter_plot_tool = ScatterPlotTool()
anomaly_highlight_tool = AnomalyHighlightTool()