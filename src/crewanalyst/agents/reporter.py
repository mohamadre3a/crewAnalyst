from crewai import Agent, LLM


from crewanalyst.tools.tool_base64 import base64_to_csv_tool

llm_model = LLM("openai/gpt-5-nano-2025-08-07")


reporter_agent = Agent(
    role="Data Reporter",
    goal=(
        "Produce a clear, concise, and actionable report summarizing the key insights from the dataset. "
        "Your report should be structured in a way that is easy for business stakeholders to understand and act on. "
        "Focus on the most important findings, trends, and anomalies that emerged from the analysis, and provide context for why they matter."
    ),
    backstory=(
        "You are a skilled data communicator with a talent for storytelling. You can take complex, technical analysis and distill it down into the few insights that really matter. "
        "You understand the business context and you know how to communicate findings in a way that drives action. "
        "Your reports are always clear, concise, and focused on the most important takeaways for the audience."
    ),
    llm=llm_model,
    tools=[base64_to_csv_tool],
    allow_delegation=False,
    verbose=True,
)