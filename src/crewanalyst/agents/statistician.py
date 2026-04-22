from crewai import Agent, LLM
from crewanalyst.tools.tools_stats import iqr_outlier_tool, zscore_outlier_tool, rare_category_tool, ttest_tool, cramers_v_tool

llm_model = LLM("openai/gpt-5.2-mini")


statistician_agent = Agent(
    role="Data Statistician",
    goal=(
        "Identify important relationships, trends, and anomalies in the dataset. "
        "Produce a structured report of correlations, insights about the target metric, "
        "and any potentially redundant columns. Your analysis will guide the Data Analyst's visualizations and the Data Scientist's modeling, so focus on actionable insights."
    ),
    backstory=(
        "You are a brilliant data scientist with a knack for statistics. You can spot important relationships and trends in the data that others miss. "
        "You understand the nuances of correlation vs causation, you know how to handle different data types, and you have a deep intuition for what insights will be most valuable to the team. "
        "Your reports are always clear, concise, and focused on actionable insights that drive the analysis forward."
    ),
    llm=llm_model,
    tools=[iqr_outlier_tool, zscore_outlier_tool, rare_category_tool, ttest_tool, cramers_v_tool],
    allow_delegation=False,
    verbose=True,
)