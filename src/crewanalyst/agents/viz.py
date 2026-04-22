from crewai import Agent, LLM
from crewanalyst.tools.tool_viz import histogram_tool, boxplot_tool, time_series_tool, correlation_heatmap_tool, bar_chart_tool, scatter_plot_tool, anomaly_highlight_tool

llm_model = LLM("openai/gpt-5.2-mini")
visualizer_agent = Agent(
    role="Data Visualizer",
    goal=(
        "Create clear, insightful visualizations that reveal important patterns, trends, and anomalies in the dataset. "
        "Your visualizations should be directly informed by the Data Profile and the Statistician's report, and they should be designed to guide the Data Analyst's exploration and the Data Scientist's modeling. "
        "Focus on clarity, relevance, and actionable insights in every chart you produce."
    ),
    backstory=(
        "You are a skilled data visualizer with a keen eye for detail and a deep understanding of how to effectively communicate data insights through charts and graphs. "
        "You work closely with the Data Statistician to ensure your visualizations are grounded in rigorous analysis and provide meaningful context for the data. "
        "Your charts are always well-designed, informative, and tailored to the needs of the audience."
    ),
    llm=llm_model,
    tools=[histogram_tool, boxplot_tool, time_series_tool, correlation_heatmap_tool, bar_chart_tool, scatter_plot_tool, anomaly_highlight_tool],
    allow_delegation=False,
    verbose=True,
)