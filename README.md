# CrewAnalyst

CrewAnalyst is an AI-powered data analysis assistant built around a simple idea: upload a CSV, add an optional one-line description, and receive a complete professional analysis report.

The user should not need to know which questions to ask, which charts to create, or which statistical checks matter. They can provide lightweight context such as "this is e-commerce transaction data" or "monthly sales by rep", and the CrewAI workflow takes it from there.

For now, CrewAnalyst is a Gradio app that profiles the uploaded database-style CSV. It classifies columns, summarizes the table shape, and flags data quality issues. The fuller analysis report workflow is the goal we are building toward.

## What We Are Building

CrewAnalyst turns raw tabular data into a shareable HTML or PDF report that includes:

- Clear summary statistics
- Useful charts and visual breakdowns
- Anomaly and outlier detection
- Correlations and relationships in the data
- Narrative insights written in plain language
- Practical observations a business user can act on

## The Goal

Our goal is to make exploratory data analysis feel effortless. A user should be able to upload a dataset and get back the kind of polished, structured report they would expect from a data analyst, without writing code or answering a long series of follow-up questions.

CrewAnalyst is designed to be the first pass analyst: fast, thorough, and ready to produce a report that can be shared with a team, client, or stakeholder.

## Setup

This project uses Python >=3.10 and <3.14 with `uv`.

Install dependencies:

```bash
uv sync
```

Create your local environment file:

```bash
cp .env.example .env
```

Then add your API key to `.env`.

Given that I used `openai` as the default provider, you can get an API key from [OpenAI](https://platform.openai.com/account/api-keys) and add it to your `.env`:

```text
OPENAI_API_KEY=your_api_key_here
```

Note that if you wish to change the provider, you have to also change the LLMs loaded in agents folder.

## Running The Gradio App

Start the app from the project root:

```bash
uv run app.py
```

Gradio will print a local URL, usually:

```text
http://127.0.0.1:7860
```

Open that URL in your browser, upload a CSV, and click **Run Profiler**.

## Current Scope

The current Gradio app only runs the profiling step. It does not yet generate the full HTML or PDF report with charts, statistics, anomalies, correlations, and narrative insights.
