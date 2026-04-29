from pydantic import BaseModel, Field
from typing import Literal

class Anomaly(BaseModel):
    column: str = Field(description="Column where the anomaly was detected")
    row_index: int | None = Field(default=None, description="Row index of the anomalous value, None if anomaly is column-level not row-level")
    value: str = Field(description="The anomalous value as a string for consistent formatting across types")
    detection_method: Literal["iqr", "zscore", "both", "rare_category", "cross_column"] = Field(
        description="Which method flagged this anomaly. 'both' means IQR and zscore agreed"
    )
    severity: Literal["high", "medium", "low"] = Field(
        description="high: likely impactful, medium: worth investigating, low: minor irregularity"
    )
    is_data_quality_issue: bool = Field(
        description="True if this looks like a data entry error or pipeline bug, False if it looks like a real signal"
    )
    interpretation: str = Field(
        description="One concise sentence explaining why this was flagged and what it might mean in the dataset domain"
    )
    
    
    
class AnomalyReport(BaseModel):
    anomalies: list[Anomaly] = Field(default_factory=list, description="Up to 20 representative anomalies, sorted by severity descending")
    total_found: int = Field(description="Total count of anomalies detected")
    omitted_anomaly_count: int = Field(default=0, description="Number of detected anomalies omitted from the detailed anomalies list")
    high_severity_count: int = Field(description="Number of high severity anomalies")
    medium_severity_count: int = Field(description="Number of medium severity anomalies")
    low_severity_count: int = Field(description="Number of low severity anomalies")
    columns_with_no_anomalies: list[str] = Field(default_factory=list, description="Columns that were checked and came back clean")
    summary: str = Field(description="One paragraph overview of the anomaly landscape — what was found, how severe, and what to watch out for")
    
    
