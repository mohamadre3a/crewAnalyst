from crewai import Task
from crewanalyst.agents.profiler import profiler_agent
from crewanalyst.agents.statistician import statistician_agent
from crewanalyst.agents.anomaly import anomaly_agent
from crewanalyst.agents.correlation import correlation_agent
from crewanalyst.agents.viz import visualizer_agent
from crewanalyst.agents.synthesizer import synthesizer_agent
from crewanalyst.agents.reporter import reporter_agent

from crewanalyst.schema.profile import DataProfile
from crewanalyst.schema.stats import StatsProfile
from crewanalyst.schema.anomalies import AnomalyReport
from crewanalyst.schema.correlations import CorrelationReport
from crewanalyst.schema.visualizations import VizManifest
from crewanalyst.schema.synthesis import ExecutiveSynthesis

def build_tasks(csv_path: str, user_context: str = ""):

    context_line = f"The user describes this dataset as: '{user_context}'." if user_context else ""

    # ── Task 1: Profile the dataset ──
    # tools available to the profiler_agent: inspect_csv, get_null_report
    # column profile includes name, dtype, missing_values, missing_values_percentage,
    # semantic_role (identifier, categorical, numerical, datetime, text), and is_target_metric (boolean)
    
    # data profile includes row_count, column_count, a list of column profiles,
    # inferred_domain, quality_flags (list of plain English warnings), has_datetime_index (boolean), and has_target_metric (boolean)

    
    profile_task = Task(
        description=(
            f"Profile the dataset located at: {csv_path}. {context_line} "
            "Step 1: call inspect_csv to get shape, dtypes, and a sample. "
            "Step 2: call get_null_report to get missing value counts. "
            "Step 3: using what you observed, classify every column with a semantic_role. "
            "Use 'target_metric' for the main outcome variable, 'identifier' for ID columns, "
            "You should try to come up with a meaningful target_metric if it's not obvious — it doesn't have to be perfect, just make your best guess. "
            "'categorical' for low-cardinality string columns, 'numerical' for continuous numbers, "
            "'datetime' for date/time columns, 'text' for high-cardinality free text. "
            "Step 4: infer the domain this dataset belongs to, which will help guide the rest of your analysis. You can use clues like column names, values, and the user's description to make your best guess. the inferred domain should be stored in the inferred_domain field."
            "Step 5: write quality_flags for any columns with high nulls, suspicious values, or "
            "constant values. Set has_datetime_index and has_target_metric based on your classifications."
        ),
        expected_output=(
            "A complete DataProfile object with: row_count, column_count, inferred_domain, "
            "a ColumnProfile for every column including its semantic_role and missing value stats, "
            "a list of quality_flags as plain English warnings, "
            "has_datetime_index set to True if any column is classified as datetime, "
            "has_target_metric set to True if any column is classified as target_metric."
        ),
        output_pydantic=DataProfile,
        agent=profiler_agent,
    )
    
    stats_task = Task(
        description=(
            f"Analyze the dataset at: {csv_path}. "
            "You have already been given the DataProfile from the profiler. "
            "Step 1: for every column with semantic_role 'numerical' or 'target_metric', "
            "call descriptive_stats_tool to get mean, median, std, skewness, kurtosis, min, max, p25, p75. "
            "Step 2: for every column with semantic_role 'categorical' or 'identifier', "
            "call compute_categorical_stats to get mode, unique count, entropy, top values. "
            "Step 3: if has_datetime_index is True in the profile, call analyze_datetime_column "
            "for each numerical column paired with the datetime column. "
            "Step 4: if grouping variables (categorical columns) exist alongside numerical columns, "
            "call compute_group_aggregates for the most meaningful numeric-categorical pairs. "
            "Step 5: write 3-5 key_findings as plain English observations about what stands out."
        ),
        expected_output=(
            "A StatsProfile containing: numeric_summaries for all numerical columns, "
            "categorical_summaries for all categorical columns, "
            "group_comparisons if grouping variables exist (empty list if not), "
            "time_trends if a datetime column exists (empty list if not), "
            "and 3-5 key_findings as plain English observations."
        ),
        output_pydantic=StatsProfile,
        agent=statistician_agent,
        context=[profile_task],         
        async_execution=True,          
    )
    
    anomaly_task = Task(
        description=(
            f"Detect anomalies in the dataset at: {csv_path}. "
            "You have already been given the DataProfile from the profiler. "
            "Step 1: for every column with semantic_role 'numerical' or 'target_metric', "
            "call detect_outliers_iqr and detect_outliers_zscore. "
            "If both methods flag the same row, mark detection_method as 'both' — "
            "this indicates a stronger anomaly. "
            "Step 2: for every column with semantic_role 'categorical', "
            "call detect_rare_categories to find suspicious rare values. "
            "Step 3: for each anomaly found, decide: is this a data quality issue "
            "(entry error, pipeline bug) or a real signal (genuine outlier)? "
            "Use the inferred_domain from the profile to inform your interpretation. "
            "Step 4: assign severity — high if the value is extreme and impactful, "
            "medium if worth investigating, low if minor. "
            "Step 5: return at most 20 detailed anomalies total, sorted by severity descending. "
            "Prefer high and medium severity items. If more than 20 anomalies are found, "
            "summarize the remainder in summary and set omitted_anomaly_count. "
            "Step 6: keep each anomaly interpretation to one concise sentence under 25 words. "
            "Step 7: write a one-paragraph summary of the overall anomaly landscape."
        ),
        expected_output=(
            "An AnomalyReport containing: at most 20 Anomaly objects sorted by severity descending, "
            "total_found count, high/medium/low severity counts, "
            "omitted_anomaly_count for any detected anomalies not listed in detail, "
            "columns_with_no_anomalies list, and a one-paragraph summary."
        ),
        output_pydantic=AnomalyReport,
        agent=anomaly_agent,
        context=[profile_task],        
        async_execution=True,           
    )
    
    correlation_task = Task(
        description=(
            f"Find relationships between variables in the dataset at: {csv_path}. "
            "You have already been given the DataProfile from the profiler. "
            "Step 1: call get_pearson_correlation_matrix for all numerical columns. "
            "For each pair with |r| > 0.3, create a Correlation object. "
            "Mark is_redundant=True if |r| > 0.95. "
            "Step 2: for categorical column pairs, call compute_cramers_v. "
            "Step 3: if a target_metric column exists, focus your analysis on which "
            "columns correlate most strongly with it — these go in target_metric_correlations. "
            "Step 4: write a one-paragraph summary of the most important relationships found. "
            "Do not compute correlations involving identifier columns."
        ),
        expected_output=(
            "A CorrelationReport containing: top_correlations sorted by absolute coefficient descending, "
            "target_metric_correlations if a target metric exists (empty list if not), "
            "redundant_pairs for near-perfect correlations, "
            "total_pairs_tested count, and a one-paragraph summary."
        ),
        output_pydantic=CorrelationReport,
        agent=correlation_agent,
        context=[profile_task],        
        async_execution=True,          
    )
    
    
    viz_generate_task = Task(
        description=(
            f"Generate charts for the dataset at: {csv_path}. "
            "You have the outputs from the statistician, anomaly detector, and correlation analyst. "
            "Your ONLY job here is to call chart-generation tools for findings that warrant a visualization. "
            "You MUST actually call the tools — producing zero tool calls is invalid output.\n\n"
            "Guidelines for which tool to call:\n"
            "- For skewed numerical columns flagged by the statistician: call generate_histogram.\n"
            "- For group comparisons with meaningful differences: call generate_boxplot.\n"
            "- For strong correlations (|r| > 0.5): call generate_scatter_plot.\n"
            "- If 2+ numeric columns exist: call generate_correlation_heatmap.\n"
            "- For datetime data: call generate_time_series_chart.\n"
            "- For high-severity anomalies: call generate_anomaly_highlight_chart.\n"
            "- For dominant categorical values: call generate_bar_chart.\n"
            "Generate at most 10 charts total.\n\n"
            "After all tool calls, your final answer must be ONLY a newline-separated list "
            "of the file paths the tools returned — one path per line, nothing else. "
            "No JSON, no commentary, no markdown."
        ),
        expected_output=(
            "A newline-separated list of file paths returned by the chart tools. "
            "Each line is one file path string. Nothing else."
        ),
        agent=visualizer_agent,
        context=[profile_task, stats_task, anomaly_task, correlation_task],
        async_execution=False,
    )

    viz_manifest_task = Task(
        description=(
            "Using the file paths from the previous step (one per line) and the analysis context, "
            "assemble the VizManifest. Do not call any tools.\n\n"
            "For each file path from the previous step, create one Chart object with:\n"
            "- file_path: the EXACT path string from the previous step, character-for-character\n"
            "- chart_type: inferred from filename/context (histogram, boxplot, scatter, line, bar, heatmap, correlation_heatmap)\n"
            "- title: short descriptive title (e.g., 'Distribution of Revenue')\n"
            "- caption: one sentence on what the chart shows and why it matters\n"
            "- finding_source: 'statistics', 'anomalies', or 'correlations'\n"
            "- finding_it_illustrates: plain-English description of the specific finding\n"
            "- columns_used: column names appearing in the chart\n\n"
            "Only use file paths that appear verbatim in the previous step's output. "
            "Do not invent paths. If you considered a finding but no path exists for it, "
            "list it in skipped_visualizations with a brief reason."
        ),
        expected_output=(
            "A complete VizManifest with one Chart per file path from the previous step, "
            "total_charts set correctly, and skipped_visualizations populated for any "
            "findings not visualized."
        ),
        output_pydantic=VizManifest,
        agent=visualizer_agent,
        context=[viz_generate_task, profile_task, stats_task, anomaly_task, correlation_task],
        async_execution=False,
)
    
    synthesis_task = Task(
        description=(
            "You have the complete outputs from all analysis agents: "
            "the DataProfile, StatsSummary, AnomalyReport, CorrelationReport, and VizManifest. "
            "Step 1: identify the 3-5 most important findings across all analyses. "
            "Rank them by importance and note which agent produced each finding. "
            "Mark actionable=True if a business user could take a concrete action based on it. "
            "Step 2: write a 2-3 paragraph executive_summary for a non-technical stakeholder. "
            "No jargon. Focus on what the data says and what it means, not how you computed it. "
            "Step 3: list what the data cannot answer given available columns and quality. "
            "Step 4: write 3 concrete recommended_next_steps grounded in what was actually found. "
            "Step 5: assess overall_data_quality_assessment as 'good', 'acceptable', or 'poor'. "
            "If not 'good', write a quality_caveat explaining the main concerns."
        ),
        expected_output=(
            "An ExecutiveSynthesis containing: key_findings ranked list, "
            "executive_summary as 2-3 readable paragraphs, "
            "what_data_cannot_answer list, recommended_next_steps list, "
            "overall_data_quality_assessment, and quality_caveat if quality is not good."
        ),
        output_pydantic=ExecutiveSynthesis,
        agent=synthesizer_agent,
        context=[profile_task, stats_task, anomaly_task, correlation_task, viz_manifest_task],
        async_execution=False,
    )
    report_task = Task(
    description=(
        f"Compose the final markdown report for the dataset at: {csv_path}. "
        "All analysis outputs are available in your context: DataProfile, StatsProfile, "
        "AnomalyReport, CorrelationReport, VizManifest, and ExecutiveSynthesis.\n\n"

        "Your ENTIRE response must be the markdown content of the report, and nothing else. "
        "Do not add any preamble, explanation, or commentary. Do not wrap it in code fences. "
        "Do not call any tools. Just emit the markdown directly as your final answer.\n\n"

        "Use this structure:\n"
        "  # Dataset Analysis Report\n"
        "  ## Executive Summary       (from ExecutiveSynthesis.executive_summary)\n"
        "  ## Key Findings            (ranked list; flag actionable ones)\n"
        "  ## Dataset Overview        (rows, columns, inferred_domain, quality_flags)\n"
        "  ## Statistical Highlights  (interesting items from StatsProfile.key_findings; "
        "                              use markdown tables for numeric summaries)\n"
        "  ## Anomalies               (top items + summary paragraph)\n"
        "  ## Relationships           (top correlations + summary paragraph)\n"
        "  ## Visualizations          (one subsection per chart, see below)\n"
        "  ## What This Data Cannot Answer\n"
        "  ## Recommended Next Steps\n"
        "  ## Data Quality Assessment (overall + caveat if any)\n\n"

        "For each chart in VizManifest.charts, embed it as:\n"
        "  ### {chart.title}\n"
        "  ![{chart.title}](charts/{filename})\n"
        "  *{chart.caption}*\n"
        "  > Illustrates: {chart.finding_it_illustrates}\n\n"
        "  Where {filename} is the basename of chart.file_path. If file_path is "
        "  'outputs/charts/revenue_dist.png', use 'charts/revenue_dist.png'.\n\n"

        "Style: engaging plain-English prose. Use bullet lists where natural and "
        "markdown tables where structured numbers help. Do not invent values."
    ),
    expected_output=(
        "The complete markdown report content. The first character must be '#' "
        "(the top-level heading). Nothing else — no preamble, no fences, no tool calls."
    ),
    agent=reporter_agent,
    context=[
        profile_task,
        stats_task,
        anomaly_task,
        correlation_task,
        viz_manifest_task,
        synthesis_task,
    ],
    async_execution=False,
    output_file="outputs/report.md",   
)
    
    
    return [profile_task, stats_task, anomaly_task, correlation_task, viz_generate_task, viz_manifest_task, synthesis_task, report_task]
