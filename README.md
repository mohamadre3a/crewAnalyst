# CrewAnalyst

## How It Works

The pipeline has one sequential gate, then a parallel middle, then three sequential finishing steps.

```
CSV file
   │
   ▼
[1] Profile              (sequential — all other steps depend on this)
   │
   ├──────────────────────────────────────────┐
   ▼                     ▼                   ▼
[2] Statistician    [3] Anomaly         [4] Correlation    ← run in parallel
   │                     │                   │
   └──────────────────────────────────────────┘
                          │
                          ▼
                    [5] Visualizer        (waits for 2, 3, 4)
                          │
                          ▼
                    [6] Synthesizer       (waits for 1–5)
                          │
                          ▼
                    [7] Reporter          (waits for 1–6)
```

---

**Step 1 — Profile** · `profiler_agent` · *claude-haiku*

First step, always sequential. Classifies every column and produces the `DataProfile` that all other agents receive.

| Tool | What it does |
|---|---|
| `inspect_csv` | Loads the CSV; returns row count, column count, dtypes, and a 10-row sample (first 5 + last 5). |
| `get_null_report` | Returns null count and null percentage for every column. |

Output — `DataProfile`: per-column `semantic_role` (`identifier`, `categorical`, `numerical`, `datetime`, `target_metric`, `text`), `inferred_domain`, `quality_flags`, `has_datetime_index`, `has_target_metric`.

---

**Steps 2, 3, 4 — run in parallel** (each receives only the `DataProfile` as context)

---

**Step 2 — Statistician** · `statistician_agent` · *claude-sonnet*

Computes descriptive statistics, group comparisons, time trends, and surfaces 3–5 plain-English key findings.

| Tool | What it does |
|---|---|
| `get_descriptive_stats` | Mean, median, std, skewness, kurtosis, min, max, p25, p75 for a list of numeric columns. |
| `compute_categorical_stats` | Unique count, top value, top frequency, and top-20 value counts for categorical columns; also flags likely identifiers (>80% unique values). |
| `compute_group_aggregates` | Group size and mean of a numeric metric broken down by a categorical column. |
| `analyze_datetime_column` | Trend direction (`upward` / `downward` / `flat`) of a numeric metric over a datetime column, plus start/end time and gap/outlier flags. |

Output — `StatsProfile`: `numeric_stats` (mean, median, std, skewness, kurtosis, min, max, p25, p75 per numerical column), `categorical_stats` (unique count, top value, frequency, value counts per categorical column), `group_comparisons`, `time_trends`, `key_findings`.

---

**Step 3 — Anomaly Detection** · `anomaly_agent` · *claude-haiku*

Cross-references IQR and Z-score results — anomalies flagged by both are elevated in severity. Interprets every finding in the context of the inferred domain.

| Tool | What it does |
|---|---|
| `detect_outliers_iqr` | IQR outlier scan per numerical column. |
| `detect_outliers_zscore` | Z-score outlier scan per numerical column. |
| `detect_rare_categories` | Rare-value scan per categorical column (catches typos and entry errors). |

Output — `AnomalyReport`: up to 20 `Anomaly` objects sorted by severity descending, each with `column`, `row_index`, `value`, `detection_method` (`iqr` / `zscore` / `both` / `rare_category`), `severity` (`high` / `medium` / `low`), `is_data_quality_issue`, and a one-sentence `interpretation`. Also reports `total_found`, `omitted_anomaly_count`, severity counts, `columns_with_no_anomalies`, and a `summary` paragraph.

---

**Step 4 — Correlation** · `correlation_agent` · *claude-haiku*

Finds the strongest relationships between variables. Focuses on the target metric column when one exists. Never computes correlations on identifier columns.

| Tool | What it does |
|---|---|
| `get_pearson_correlation_matrix` | Full Pearson correlation matrix for all numeric columns. |
| `compute_cramers_v` | Cramér's V for categorical-to-categorical pairs. |
| `get_descriptive_stats` | Mean, median, std, skewness, kurtosis, min, max, p25, p75 for specified numeric columns. |

Output — `CorrelationReport`: `top_correlations` sorted by absolute coefficient, `target_metric_correlations` (if a target exists), `redundant_pairs` (|r| > 0.95), `total_pairs_tested`, and a `summary` paragraph. Each correlation includes coefficient, method, direction, strength label, and a plain-English sentence.

---

**Step 5 — Visualizer** · `visualizer_agent` · *claude-sonnet*

Receives outputs from steps 1–4. Generates only charts that illustrate a specific finding — maximum 10 charts total.

| Tool | What it does |
|---|---|
| `generate_histogram` | Histogram + KDE curve for a numeric column; used for skewed or interesting distributions. |
| `generate_boxplot` | Grouped box plot of a numeric metric across categories; used when group differences are meaningful. |
| `generate_time_series_chart` | Line chart over time; optionally splits by a categorical column. Only used when a datetime column exists. |
| `generate_correlation_heatmap` | Pearson correlation heatmap for all numeric columns; used when multiple correlations are worth showing together. |
| `generate_bar_chart` | Horizontal bar chart of the top N most frequent values in a categorical column. |
| `generate_scatter_plot` | Scatter plot of two numeric columns; optionally colors points by a category. Used for strong correlations (|r| > 0.5). |
| `generate_anomaly_highlight_chart` | Index scatter plot with anomalous rows highlighted in red. Used for high-severity anomalies. |

Output — `VizManifest`: list of `Chart` objects (title, caption, chart_type, finding_source, finding_it_illustrates, columns_used, file_path) and `skipped_visualizations` noting what was considered but not charted. PNG files saved to `outputs/charts/`.

---

**Step 6 — Synthesizer** · `synthesizer_agent` · *claude-sonnet*

Receives all prior outputs. No tools — works entirely from structured context.

Output — `ExecutiveSynthesis`: `key_findings` ranked list (each tagged `actionable: true/false`), 2–3 paragraph `executive_summary` in plain English for a non-technical audience, `what_data_cannot_answer`, `recommended_next_steps` (3 concrete actions grounded in the findings), `overall_data_quality_assessment` (`good` / `acceptable` / `poor`), and a `quality_caveat` if quality is not good.

---

**Step 7 — Reporter** · `reporter_agent` · *claude-haiku*

Receives all prior outputs and composes the full report. The markdown is saved automatically to `outputs/report.md` by CrewAI (`output_file`). The agent can then convert it to PDF.

| Tool | What it does |
|---|---|
| `write_markdown_report` | Writes the complete markdown string to `outputs/report.md` with chart references as relative paths. |
| `convert_markdown_to_pdf` | Converts the saved markdown to a styled A4 PDF at `outputs/report.pdf` using WeasyPrint; charts embed inline. |

Report sections: Executive Summary · Key Findings · Dataset Overview · Statistical Highlights · Anomalies · Relationships · Visualizations (one subsection per chart) · What This Data Cannot Answer · Recommended Next Steps · Data Quality Assessment.

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
