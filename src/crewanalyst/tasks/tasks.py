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
    
    return [profile_task]
