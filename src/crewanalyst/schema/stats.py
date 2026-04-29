from pydantic import BaseModel, Field
from typing import Literal
# Literal["target_metric","identifier", "categorical", "numerical", "datetime", "text"] 
class NumericColumnStats(BaseModel):
    """Statistics for a numeric column."""
    mean: float = Field(description="Mean of the column")
    median: float = Field(description="Median of the column")
    std_dev: float = Field(description="Standard deviation of the column")
    min: float = Field(description="Minimum value in the column")
    max: float = Field(description="Maximum value in the column")
    skewness: float = Field(description="Skewness of the column")
    kurtosis: float = Field(description="Kurtosis of the column")
    p25: float = Field(description="25th percentile of the column")
    p75: float = Field(description="75th percentile of the column")
    
    
    
class CategoricalColumnStats(BaseModel):
    """Statistics for a categorical column."""
    unique_values: int = Field(description="Number of unique values in the column")
    top_value: str = Field(description="Most frequent value in the column")
    top_freq: int = Field(description="Frequency of the most frequent value")
    unique_value_counts: dict = Field(description="Dictionary mapping unique values to their counts")
    is_identifier: bool = Field(description="True if the column is classified as an identifier")
    
class GroupStats(BaseModel):
    group_name: str = Field(description="Name of the group (e.g., 'Male', 'Female')")
    group_size: int = Field(description="Number of rows in the group")
    group_mean: float = Field(description="Mean of the numeric column for the group")
    is_identifier: bool = Field(description="True if the categorical column is classified as an identifier")

class GroupComparison(BaseModel):
    """Comparison of a numeric column across groups defined by a categorical column."""
    numeric_column: str = Field(description="Name of the numeric column being compared")
    categorical_column: str = Field(description="Name of the categorical column defining the groups")
    groups: list[GroupStats] = Field(description="List of statistics for each group")

    
class TimeTrend(BaseModel):
    """Trend analysis for a numeric column over time."""
    start_time: str = Field(description="Start time of the trend analysis")
    end_time: str = Field(description="End time of the trend analysis")
    
    inferred_frequency: str = Field(description="Frequency of the time intervals (e.g., 'D' for daily, 'M' for monthly)")
    trend_direction: Literal["upward", "downward", "flat", "unclear"] = Field(description="Direction of the trend")
    trend_note: str = Field(description="Plain English note about the trend, e.g. 'Revenue has been steadily increasing over the past year with a noticeable spike in December.'")
    
    gaps_detected: bool = Field(description="True if there are gaps in the time series data")
    outliers_detected: bool = Field(description="True if there are outliers in the time series data")
    
    
class StatsProfile(BaseModel):
    """Comprehensive statistics profile for a dataset."""
    numeric_stats: dict[str, NumericColumnStats] = Field(description="Dictionary mapping numeric column names to their statistics")
    categorical_stats: dict[str, CategoricalColumnStats] = Field(description="Dictionary mapping categorical column names to their statistics")
    group_comparisons: list[GroupComparison] = []
    time_trends: dict[str, TimeTrend] = Field(description="Dictionary mapping numeric column names to their time trend analyses")
    key_findings: list[str] = Field(description="List of plain English key findings from the statistical analysis, e.g. 'The average revenue is higher for customers in the 'Gold' segment compared to the 'Silver' segment.'")