# crew.py

import asyncio
from dotenv import load_dotenv
from crewai import Crew, Process

from agents.profiler import profiler_agent
from agents.statistician import statistician_agent
from agents.anomaly import anomaly_agent
from agents.correlation import correlation_agent
from agents.viz import visualizer_agent
from agents.synthesizer import synthesizer_agent
from agents.reporter import reporter_agent
from tasks.tasks import build_tasks

load_dotenv()


def run(csv_path: str, user_context: str = ""):

    tasks = build_tasks(csv_path, user_context)

    crew = Crew(
        agents=[
            profiler_agent,
            statistician_agent,
            anomaly_agent,
            correlation_agent,
            visualizer_agent,
            synthesizer_agent,
            reporter_agent,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    run(
        csv_path="sample_data/test1.csv",
        user_context="",
    )