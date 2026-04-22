from pydantic import BaseModel, Field
from typing import Literal

class Chart(BaseModel):
    title: str = Field(description="Chart title as it will appear in the report")
    caption: str = Field(description="One sentence explaining what this chart shows and why it matters")
    chart_type: Literal[
        "histogram",
        "boxplot",
        "bar",
        "line",
        "scatter",
        "heatmap",
        "correlation_heatmap"
    ] = Field(description="Type of chart generated")
    finding_source: Literal["statistics", "anomalies", "correlations"] = Field(
        description="Which analysis agent produced the finding this chart illustrates"
    )
    finding_it_illustrates: str = Field(
        description="Plain English description of the specific finding this chart is visualizing"
    )
    columns_used: list[str] = Field(description="Column names that appear in this chart")
    file_path: str = Field(description="Absolute path to the saved PNG file")
    base64_data: str | None = Field(
        default=None,
        description="Base64 encoded PNG string for HTML embedding — populated by the reporter agent"
    )

class VizManifest(BaseModel):
    charts: list[Chart] = Field(description="All generated charts in the order they should appear in the report")
    total_charts: int = Field(description="Total number of charts generated")
    skipped_visualizations: list[str] = Field(
        default_factory=list,
        description="Findings the viz agent considered but decided did not warrant a chart, with a brief reason each"
    )