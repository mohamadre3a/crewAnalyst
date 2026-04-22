from pydantic import BaseModel, Field
from typing import Literal

class KeyFinding(BaseModel):
    rank: int = Field(description="Importance rank, 1 being the most important finding overall")
    finding: str = Field(description="The finding stated clearly in one or two sentences")
    source: str = Field(description="Which agent or analysis this came from e.g. 'anomaly detection', 'correlation analysis'")
    actionable: bool = Field(
        description="True if a business user could take a concrete action based on this finding"
    )

class ExecutiveSynthesis(BaseModel):
    key_findings: list[KeyFinding] = Field(
        description="Top 3 to 5 findings ranked by importance, drawn from across all analyses"
    )
    executive_summary: str = Field(
        description="2 to 3 paragraph narrative written for a non-technical stakeholder — no jargon, focus on what the data says and what it means"
    )
    what_data_cannot_answer: list[str] = Field(
        description="Honest list of questions the analysis cannot address given the available columns and data quality"
    )
    recommended_next_steps: list[str] = Field(
        description="3 concrete follow-up questions or analyses worth pursuing, grounded in what was actually found"
    )
    overall_data_quality_assessment: Literal["good", "acceptable", "poor"] = Field(
        description="High level quality verdict: good means analysis is reliable, acceptable means results are usable with caveats, poor means findings should be treated with significant skepticism"
    )
    quality_caveat: str | None = Field(
        default=None,
        description="If quality is acceptable or poor, a plain English explanation of the main data quality concerns affecting reliability — None if quality is good"
    )