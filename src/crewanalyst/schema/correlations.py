from pydantic import BaseModel, Field
from typing import Literal

class Correlation(BaseModel):
    column_a: str = Field(description="First column in the relationship")
    column_b: str = Field(description="Second column in the relationship")
    coefficient: float = Field(description="Correlation coefficient — Pearson r for numeric pairs, Cramers V for categorical pairs")
    method: Literal["pearson", "cramers_v", "point_biserial"] = Field(
        description="Statistical method used. pearson for numeric-numeric, cramers_v for categorical-categorical, point_biserial for numeric-categorical"
    )
    direction: Literal["positive", "negative", "none"] = Field(
        description="Direction of the relationship. 'none' for Cramers V which has no direction"
    )
    strength: Literal["strong", "moderate", "weak"] = Field(
        description="strong: |r|>0.7 or V>0.5, moderate: |r|>0.4 or V>0.3, weak: everything below that"
    )
    plain_english: str = Field(
        description="One sentence explanation of this relationship in plain English, referencing the domain context"
    )
    is_redundant: bool = Field(
        default=False,
        description="True if |coefficient| > 0.95 suggesting these columns carry nearly identical information"
    )

class CorrelationReport(BaseModel):
    top_correlations: list[Correlation] = Field(
        description="All meaningful correlations found, sorted by absolute coefficient descending"
    )
    target_metric_correlations: list[Correlation] = Field(
        default_factory=list,
        description="Subset of correlations involving the target metric column — empty if no target metric exists"
    )
    redundant_pairs: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Column pairs with near-perfect correlation flagged as potentially redundant"
    )
    total_pairs_tested: int = Field(description="Total number of column pairs that were evaluated")
    summary: str = Field(
        description="One paragraph narrative of the most important relationships in the data and what they suggest"
    )