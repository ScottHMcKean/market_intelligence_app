"""Debug script to find and test MLflow traces."""

import mlflow
import os
from src.config import DatabricksConfig

# Set MLflow tracking URI
os.environ["MLFLOW_TRACKING_URI"] = "databricks://aws"

# Load config
config = DatabricksConfig.from_config()
print(f"📋 Experiment name: {config.experiment_name}")

# Set up MLflow
mlflow.set_tracking_uri("databricks://aws")
mlflow.set_experiment(experiment_name=config.experiment_name)

# Get experiment
experiment = mlflow.get_experiment_by_name(config.experiment_name)
if not experiment:
    print(f"❌ Experiment not found: {config.experiment_name}")
    exit(1)

print(f"✅ Found experiment: {experiment.name} (ID: {experiment.experiment_id})")

# Search for recent traces
print(f"\n🔍 Searching for recent traces...")
traces = mlflow.search_traces(
    experiment_ids=[experiment.experiment_id], max_results=10, order_by=["timestamp_ms DESC"]
)

if traces is not None and not traces.empty:
    print(f"\n✅ Found {len(traces)} traces:")
    print("\n" + "=" * 100)

    for idx, trace_row in traces.iterrows():
        trace_id = trace_row.get("trace_id")  # Changed from request_id
        request_id = trace_row.get("client_request_id")
        timestamp = trace_row.get("request_time")  # Changed from timestamp_ms
        status = trace_row.get("state")  # Changed from status

        print(f"\nTrace {idx + 1}:")
        print(f"   Trace ID: {trace_id}")
        print(f"   Client Request ID: {request_id}")
        print(f"   Timestamp: {timestamp}")
        print(f"   State: {status}")

        # Show all columns
        print(f"   Available columns: {list(trace_row.index)}")

        # Look for the specific trace
        if trace_id and "cbc5191e533a93c8235751c747595479" in str(trace_id):
            print(f"\n   🎯 FOUND TARGET TRACE!")
            print(f"   Full trace data:")
            for col in trace_row.index:
                val = trace_row[col]
                if col not in ["spans", "trace"]:  # Skip large objects
                    print(f"      {col}: {val}")

    print("\n" + "=" * 100)

    # Try to find trace by searching for partial ID
    print(f"\n🔍 Searching for trace containing 'cbc5191e533a93c8235751c747595479'...")
    target_traces = mlflow.search_traces(
        experiment_ids=[experiment.experiment_id],
        filter_string="",
        max_results=100,
        order_by=["timestamp_ms DESC"],
    )

    if target_traces is not None and not target_traces.empty:
        for idx, trace_row in target_traces.iterrows():
            trace_id = str(trace_row.get("trace_id", ""))
            if "cbc5191e533a93c8235751c747595479" in trace_id or trace_id.startswith("tr-cbc5191e"):
                print(f"\n✅ FOUND IT!")
                print(f"   Full Trace ID: {trace_id}")
                print(f"   Timestamp: {trace_row.get('request_time')}")
                print(f"   State: {trace_row.get('state')}")

                # Try to log feedback
                print(f"\n🧪 Testing feedback logging...")
                try:
                    from mlflow.entities import AssessmentSource, AssessmentSourceType

                    mlflow.log_feedback(
                        trace_id=trace_id,
                        name="test_feedback",
                        value=True,
                        source=AssessmentSource(
                            source_type=AssessmentSourceType.HUMAN,
                            source_id="debug_script@test.com",
                        ),
                    )
                    print(f"   ✅ Successfully logged feedback!")
                except Exception as e:
                    print(f"   ❌ Error logging feedback: {e}")
                    import traceback

                    traceback.print_exc()

                break

else:
    print(f"\n⚠️ No traces found in experiment")

print("\n" + "=" * 100)
print("Debug complete!")
