from pydantic import BaseModel, Field
from typing import Literal


class ColumnProfile(BaseModel):
    """Column Schema for any database."""
    name: str = Field(description="Column name as it appears in the CSV")
    dtype: str = Field(description="Data type of the column (e.g., int, float, object)")
    missing_values: int = Field(description="Number of missing values in the column")
    missing_values_percentage: float = Field(description="Percentage of missing values in the column")
    semantic_role: Literal["identifier", "categorical", "numerical", "datetime", "text"] = Field(description="Semantic role of the column")
    is_target_metric: bool = Field(description="True if this column is likely a target metric for modeling")
    
    
class DataProfile(BaseModel):
    """Data Schema for any database."""
    row_count: int = Field(description="Total number of rows in the dataset")
    column_count: int = Field(description="Total number of columns in the dataset")
    columns: list[ColumnProfile] = Field(description="List of column profiles in the dataset")
    infered_domain: str = Field(description="Inferred domain of the dataset (e.g., finance, healthcare, retail)")
    quality_flags: list[str] = Field(description="Plain English data quality warnings, e.g. 'revenue has 12% nulls'")
    has_datetime_index: bool = Field(description="True if at least one column was classified as time_index")
    has_target_metric: bool = Field(description="True if at least one column was classified as target_metric")
    
