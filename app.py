# app.py

import gradio as gr
import tempfile
import os
from dotenv import load_dotenv
from crewai import Crew, Process
from crewanalyst.agents.profiler import profiler_agent
from crewanalyst.tasks.tasks import build_tasks
from crewanalyst.schema.profile import DataProfile

load_dotenv()


def run_profiler(csv_file):
    if csv_file is None:
        return "Please upload a CSV file.", ""

    # gradio gives you a temp file path directly
    csv_path = csv_file.name

    tasks = build_tasks(csv_path=csv_path, user_context="")
    profile_task = tasks[0]  # first task is always the profile task

    crew = Crew(
        agents=[profiler_agent],
        tasks=[profile_task],
        process=Process.sequential,
        verbose=True,
    )

    crew.kickoff()

    profile: DataProfile = profile_task.output.pydantic

    if profile is None:
        return "Profiling failed — the agent could not produce a valid DataProfile.", ""

    # ── Build the summary text ──────────────────────────────────
    summary_lines = [
        f"**Domain:** {profile.inferred_domain}",
        f"**Rows:** {profile.row_count}",
        f"**Columns:** {profile.column_count}",
        f"**Has datetime column:** {profile.has_datetime_index}",
        f"**Has target metric:** {profile.has_target_metric}",
    ]
    summary = "\n".join(summary_lines)

    # ── Build the column table as markdown ──────────────────────
    table_lines = [
        "| Column | Type | Role | Missing | Missing % |",
        "|--------|------|------|---------|-----------|",
    ]
    for col in profile.columns:
        table_lines.append(
            f"| {col.name} | {col.dtype} | {col.semantic_role} "
            f"| {col.missing_values} | {col.missing_values_percentage}% |"
        )
    column_table = "\n".join(table_lines)

    # ── Quality flags ───────────────────────────────────────────
    if profile.quality_flags:
        flags = "\n".join([f"- ⚠ {flag}" for flag in profile.quality_flags])
    else:
        flags = "No quality issues detected."

    full_output = f"""
## Dataset Overview
{summary}

## Column Profiles
{column_table}

## Quality Flags
{flags}
"""
    return full_output


with gr.Blocks(title="AutoAnalyst — Profiler") as demo:
    gr.Markdown("# AutoAnalyst")
    gr.Markdown("Upload a CSV file and the profiler agent will classify every column and flag data quality issues.")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload CSV",
                file_types=[".csv"],
            )
            run_btn = gr.Button("Run Profiler", variant="primary")

        with gr.Column(scale=2):
            output = gr.Markdown(label="Profile Output")

    run_btn.click(
        fn=run_profiler,
        inputs=[file_input],
        outputs=[output],
    )

if __name__ == "__main__":
    demo.launch()