# test_profiler.py

from crewai import Crew, Task, Process
from crewanalyst.agents.profiler import profiler_agent
from crewanalyst.schema.profile import DataProfile

from dotenv import load_dotenv
load_dotenv()

csv_path = "sample_data/test1.csv"  # swap with any CSV you have

profile_task = Task(
    description=(
        f"Profile the dataset located at: {csv_path}. "
        "Use your tools to inspect the CSV structure and null values. "
        "Classify every column by its semantic role. "
        "Infer what domain this dataset belongs to. "
        "Flag any data quality issues you find."
    ),
    expected_output=(
        "A complete DataProfile containing row count, column count, "
        "a ColumnProfile for every column with its semantic role, "
        "the inferred domain, quality flags, and the has_datetime_index "
        "and has_target_metric boolean fields."
    ),
    output_pydantic=DataProfile,
    agent=profiler_agent,
)

crew = Crew(
    agents=[profiler_agent],
    tasks=[profile_task],
    process=Process.sequential,
    verbose=True,
)

result = crew.kickoff()

# Access the typed output
profile: DataProfile = profile_task.output.pydantic

print("\n" + "="*50)
print(f"Domain:        {profile.inferred_domain}")
print(f"Rows:          {profile.row_count}")
print(f"Columns:       {profile.column_count}")
print(f"Has datetime:  {profile.has_datetime_index}")
print(f"Has target:    {profile.has_target_metric}")
print("\nColumn roles:")
for col in profile.columns:
    print(f"  {col.name:<25} {col.semantic_role:<20} nulls: {col.missing_values_percentage}%")
print("\nQuality flags:")
for flag in profile.quality_flags:
    print(f"  ⚠ {flag}")