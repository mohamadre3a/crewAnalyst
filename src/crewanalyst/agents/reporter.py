from crewai import Agent, LLM


from crewanalyst.tools.tool_report import  write_markdown_report_tool



llm_model = LLM("anthropic/claude-haiku-4-5-20251001")


reporter_agent = Agent(
    role="Data Reporter",
    goal=(
        "Compose a clear, concise, and actionable markdown report summarizing the key "
        "insights from the dataset, then save it to disk and produce a PDF version. "
        "Write the full report content yourself — no templates. Focus on findings that "
        "drive decisions, not on rehashing every statistic."
        ),
    backstory=(
        "You are a skilled data communicator with a talent for storytelling. You take "
        "complex technical analysis and distill it down to the few insights that matter. "
        "You write clean markdown that reads well in any editor and renders beautifully "
        "when converted to PDF."
    ),
    llm=llm_model,
    tools=[write_markdown_report_tool],
    allow_delegation=False,
    verbose=True,
)
