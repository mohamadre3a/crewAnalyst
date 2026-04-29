I used the following prompt to generate the README.md content:

```text
Write a README.md for a project called CrewAnalyst. CrewAnalyst is a data analysis assistant built using CrewAI. It takes CSV files as input and produces structured data profiles, statistical analyses, anomaly detection, correlation insights, charts, and a synthesized HTML report. The README should explain the project's purpose, features, current status, project layout, setup instructions, how to run the profiler UI and test harness, expected outputs, and any relevant development notes. The tone should be clear and informative, targeting data analysts and developers interested in AI-powered data analysis tools.
```

This project is designed by me, and is developed by me and help of Codex and Claude Code.

# CrewAnalyst

## How It Works

The pipeline runs sequentially. Each agent receives the outputs of all prior agents before it acts.

---

**Step 1 — Read the dataset**

The CSV file path (and an optional free-text context string) is passed into the crew. No agent runs until the file path is validated.

---

**Step 2 — Profile** · `profiler_agent` · *claude-haiku*

Understands the shape, quality, and meaning of the dataset so every downstream agent has a reliable foundation.

| Tool | What it does |
|---|---|
| `inspect_csv` | Loads the CSV and returns row count, column count, data types, and a 10-row sample (first 5 + last 5). |
| `get_null_report` | Returns null count and null percentage for every column. |

Output: a structured `DataProfile` — column semantic roles (identifier, target, feature, datetime, text), inferred domain, and quality flags.

---

**Step 3 — Statistician** · `statistician_agent` · *claude-sonnet*

Identifies important relationships, trends, and group differences across the dataset.

| Tool | What it does |
|---|---|
| `detect_outliers_iqr` | Flags values below Q1 − 1.5×IQR or above Q3 + 1.5×IQR in a numeric column. |
| `detect_outliers_zscore` | Flags values whose absolute Z-score exceeds a threshold (default 3.0). |
| `detect_rare_categories` | Flags categorical values that appear in fewer than 1% of rows. |
| `run_ttest` | Runs an independent-samples t-test between two groups on a numeric metric; returns t-stat, p-value, and significance flag. |
| `compute_cramers_v` | Computes Cramér's V association strength between two categorical columns (0 = no association, 1 = perfect). |

Output: descriptive statistics, group comparisons, and a structured list of actionable insights.

---

**Step 4 — Anomaly Detection** · `anomaly_agent` · *claude-haiku*

Cross-references two outlier methods to reduce false positives and interprets anomalies in the context of the dataset domain.

| Tool | What it does |
|---|---|
| `detect_outliers_iqr` | IQR-based outlier detection (same tool as Step 3, re-run per column). |
| `detect_outliers_zscore` | Z-score-based outlier detection (used alongside IQR — agreement between both elevates severity). |
| `detect_rare_categories` | Rare-category scan for categorical columns to catch typos and data-entry errors. |

Output: a list of flagged anomalies with severity levels, limited to numerical and categorical columns (never identifiers or free text).

---

**Step 5 — Correlation** · `correlation_agent` · *claude-haiku*

Finds the strongest and most meaningful relationships between variables, with plain-English explanations for every finding.

| Tool | What it does |
|---|---|
| `get_pearson_correlation_matrix` | Computes the full Pearson correlation matrix for all numeric columns. |
| `compute_cramers_v` | Computes Cramér's V for categorical-to-categorical pairs where Pearson does not apply. |
| `get_descriptive_stats` | Computes mean, median, std, min, max, skewness, and kurtosis for specified numeric columns. |

Output: ranked correlations with coefficient, method, direction, strength label, and a plain-English sentence per pair. Near-perfect correlations (V > 0.95) are flagged as potentially redundant features.

---

**Step 6 — Visualization** · `visualizer_agent` · *claude-sonnet*

Generates charts directly informed by the profiler output and the statistician's findings.

| Tool | What it does |
|---|---|
| `generate_histogram` | Histogram with a KDE curve for a numeric column — shows distribution shape and skewness. |
| `generate_boxplot` | Grouped box plot of a numeric metric across categories — shows spread and outliers per group. |
| `generate_time_series_chart` | Line chart of a numeric metric over time; can split into multiple lines by a categorical column. |
| `generate_correlation_heatmap` | Pearson correlation heatmap for all numeric columns together. |
| `generate_bar_chart` | Horizontal bar chart of the top N most frequent values in a categorical column. |
| `generate_scatter_plot` | Scatter plot of two numeric columns; optionally colors points by a categorical grouping. |
| `generate_anomaly_highlight_chart` | Index scatter plot with anomalous rows highlighted in red. |

Output: PNG files saved to `outputs/charts/`.

---

**Step 7 — Synthesize** · `synthesizer_agent` · *claude-sonnet*

Distills all prior analysis into the 3–5 findings a business stakeholder actually needs to act on. No tools — works entirely from the structured outputs passed in by the prior agents.

Output: executive summary, key findings in plain language, limitations, and recommended next steps.

---

**Step 8 — Report** · `reporter_agent` · *claude-haiku*

Composes the full report as markdown, saves it to disk, and converts it to a styled PDF.

| Tool | What it does |
|---|---|
| `write_markdown_report` | Writes the complete markdown string to `outputs/report.md`. Chart references use relative paths so images render correctly. |
| `convert_markdown_to_pdf` | Converts the saved markdown to a styled A4 PDF at `outputs/report.pdf` using WeasyPrint; charts embed inline. |

Output: `outputs/report.md` and `outputs/report.pdf`.

---

CrewAnalyst is a CrewAI-powered data analysis assistant for CSV files. The project is being built around a simple workflow: upload a dataset, provide optional context, and let a crew of specialized analysis agents profile the data, find patterns, generate charts, synthesize findings, and assemble a stakeholder-friendly HTML report.

The currently supported UI is a Gradio profiler app. A fuller multi-agent report pipeline is already defined in the codebase and is under active wiring.

## What It Does

- Profiles a CSV file: row count, column count, data types, missing values, inferred domain, semantic column roles, and quality flags.
- Computes statistical summaries for numerical, categorical, grouped, and time-based data.
- Detects outliers and rare categories using IQR, Z-score, and frequency checks.
- Finds numerical and categorical relationships using Pearson correlation and Cramer's V.
- Generates focused charts such as histograms, box plots, bar charts, scatter plots, heatmaps, time series charts, and anomaly highlights.
- Synthesizes the most important findings into plain-language executive summaries and recommended next steps.
- Renders a report template to `outputs/report.html` when the full report workflow is run successfully.

## Current Status

The Gradio app in `app.py` runs the profiler step only. It uploads a CSV, invokes the `profiler_agent`, and displays the structured `DataProfile` result as Markdown.

The full report workflow is defined in `src/crewanalyst/tasks/tasks.py` and `src/crewanalyst/crew.py`. That pipeline includes seven agents:

- `profiler_agent`: inspects the dataset and classifies every column.
- `statistician_agent`: computes descriptive and comparative statistics.
- `anomaly_agent`: flags outliers, rare categories, and suspicious values.
- `correlation_agent`: finds meaningful relationships between variables.
- `visualizer_agent`: generates charts into `outputs/charts/`.
- `synthesizer_agent`: turns analysis outputs into executive findings.
- `reporter_agent`: embeds charts and renders `templates/report.html` to `outputs/report.html`.

The package CLI in `src/crewanalyst/main.py` still resembles the original CrewAI scaffold and is not the best entry point for the current CSV analysis workflow.

## Project Layout

```text
.
├── app.py                         # Gradio profiler UI
├── agent_tester.py                # Small profiler-only test harness
├── sample_data/test1.csv          # Sample CSV
├── templates/report.html          # HTML report template
├── outputs/                       # Generated reports and charts
├── src/crewanalyst/
│   ├── agents/                    # CrewAI agent definitions
│   ├── schema/                    # Pydantic output models
│   ├── tasks/tasks.py             # Multi-agent task builder
│   ├── tools/                     # CSV, stats, visualization, and report tools
│   ├── crew.py                    # Full workflow orchestration
│   └── main.py                    # Scaffolded package entry points
└── pyproject.toml
```

## Requirements

- Python >=3.10 and <3.14
- `uv`
- CrewAI 1.14.2
- API keys for the LLM providers used by the agents

Most current agent files instantiate Anthropic models such as `anthropic/claude-haiku-4-5-20251001` and `anthropic/claude-sonnet-4-6`, so set `ANTHROPIC_API_KEY` in your local `.env`. If you switch agents to OpenAI or another provider, update the agent `LLM(...)` definitions and provide the matching API key.

## Setup

Install dependencies:

```bash
uv sync
```

Create a local environment file:

```bash
cp .env.example .env
```

Then add the provider keys needed by the configured agents:

```text
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-4o
```

`OPENAI_API_KEY` and `MODEL` are useful if you switch any agents back to OpenAI-backed models. The current agent definitions primarily use Anthropic model names directly.

## Run The Profiler UI

From the project root:

```bash
uv run app.py
```

Gradio will print a local URL, usually:

```text
http://127.0.0.1:7860
```

Open the URL, upload a CSV, and click **Run Profiler**. The app returns a dataset overview, column profile table, and quality flags.

## Run The Profiler Test Harness

To run the profiler against `sample_data/test1.csv` without the UI:

```bash
uv run python agent_tester.py
```

This prints the inferred domain, row and column counts, column roles, and quality flags.

## Generated Outputs

When the full report workflow is wired and run, generated files are expected in:

```text
outputs/report.html
outputs/charts/*.png
```

The HTML report template includes:

- Dataset overview
- Quality flags
- Executive summary
- Key findings
- Embedded charts
- Anomaly and correlation notes
- Recommended next steps

## Development Notes

- Structured task outputs live in `src/crewanalyst/schema/`.
- CrewAI tools live in `src/crewanalyst/tools/`.
- The current Gradio app imports the profiler task directly instead of running the whole crew.
- The full task builder uses structured Pydantic outputs so downstream agents receive typed analysis context.
- Some YAML files under `src/crewanalyst/config/` still reflect the original generated CrewAI sample and are not the source of truth for the current CSV workflow.
