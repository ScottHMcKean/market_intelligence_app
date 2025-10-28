"""Test script to debug MLflow feedback logging."""

import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType
from src.config import DatabricksConfig

print("=" * 80)
print("MLflow Feedback Logging Test")
print("=" * 80)

# Load config
config = DatabricksConfig.from_config()
print(f"\n📋 Experiment name: {config.experiment_name}")
print(f"📋 Databricks host: {config.host}")

# Set up MLflow
mlflow.set_tracking_uri("databricks")
print(f"\n✅ Set tracking URI to: databricks")

# Set experiment
try:
    mlflow.set_experiment(experiment_name=config.experiment_name)
    print(f"✅ Set experiment: {config.experiment_name}")
except Exception as e:
    print(f"❌ Error setting experiment: {e}")
    exit(1)

# Get experiment
try:
    experiment = mlflow.get_experiment_by_name(config.experiment_name)
    if experiment:
        print(f"\n✅ Found experiment:")
        print(f"   - Name: {experiment.name}")
        print(f"   - ID: {experiment.experiment_id}")
        print(f"   - Artifact Location: {experiment.artifact_location}")
    else:
        print(f"\n❌ Experiment not found: {config.experiment_name}")
        exit(1)
except Exception as e:
    print(f"\n❌ Error getting experiment: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

# Search for traces
print(f"\n🔍 Searching for traces in experiment {experiment.experiment_id}...")
try:
    traces = mlflow.search_traces(
        experiment_ids=[experiment.experiment_id], max_results=5, order_by=["timestamp_ms DESC"]
    )

    if traces is not None and not traces.empty:
        print(f"\n✅ Found {len(traces)} traces:")
        print("\n" + "=" * 80)
        for idx, trace_row in traces.iterrows():
            trace_id = trace_row.get("request_id")
            timestamp = trace_row.get("timestamp_ms")
            status = trace_row.get("status")
            print(f"\nTrace {idx + 1}:")
            print(f"   - Request ID: {trace_id}")
            print(f"   - Timestamp: {timestamp}")
            print(f"   - Status: {status}")

            # Show all available columns
            print(f"   - Available columns: {list(trace_row.index)}")
        print("=" * 80)

        # Get the most recent trace
        most_recent = traces.iloc[0]
        trace_id = most_recent.get("request_id")

        print(f"\n📋 Most recent trace ID: {trace_id}")

        # Test logging feedback to this trace
        print(f"\n🧪 Testing feedback logging to trace: {trace_id}")

        user_id = "test_user@example.com"

        # Test 1: Log satisfaction feedback
        print(f"\n1️⃣ Testing log_feedback (user_satisfaction)...")
        try:
            mlflow.log_feedback(
                trace_id=trace_id,
                name="user_satisfaction",
                value=True,
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"   ✅ Successfully logged satisfaction feedback")
        except Exception as e:
            print(f"   ❌ Error logging satisfaction feedback: {e}")
            import traceback

            traceback.print_exc()

        # Test 2: Log review request
        print(f"\n2️⃣ Testing log_feedback (flagged_for_review)...")
        try:
            mlflow.log_feedback(
                trace_id=trace_id,
                name="flagged_for_review",
                value=True,
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"   ✅ Successfully logged review request")
        except Exception as e:
            print(f"   ❌ Error logging review request: {e}")
            import traceback

            traceback.print_exc()

        # Test 3: Log correction/expectation
        print(f"\n3️⃣ Testing log_expectation (user_correction)...")
        try:
            mlflow.log_expectation(
                trace_id=trace_id,
                name="user_correction",
                value=["This is a test correction from the debug script"],
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"   ✅ Successfully logged correction")
        except Exception as e:
            print(f"   ❌ Error logging correction: {e}")
            import traceback

            traceback.print_exc()

        # Try to retrieve the trace again to see if feedback was added
        print(f"\n🔍 Retrieving trace again to check for feedback...")
        try:
            traces_after = mlflow.search_traces(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"request_id = '{trace_id}'",
                max_results=1,
            )

            if traces_after is not None and not traces_after.empty:
                trace_after = traces_after.iloc[0]
                print(f"   ✅ Retrieved trace")
                print(f"   - Columns: {list(trace_after.index)}")

                # Check for feedback-related columns
                feedback_cols = [
                    col
                    for col in trace_after.index
                    if "feedback" in col.lower() or "assessment" in col.lower()
                ]
                if feedback_cols:
                    print(f"   - Feedback columns: {feedback_cols}")
                    for col in feedback_cols:
                        print(f"     - {col}: {trace_after[col]}")
                else:
                    print(f"   ⚠️ No feedback columns found")
            else:
                print(f"   ❌ Could not retrieve trace after feedback")
        except Exception as e:
            print(f"   ❌ Error retrieving trace: {e}")
            import traceback

            traceback.print_exc()

    else:
        print(f"\n⚠️ No traces found in experiment")
        print(f"\nThis means the agent is not logging traces to this experiment.")
        print(f"The traces might be in a different experiment or not being logged at all.")

except Exception as e:
    print(f"\n❌ Error searching traces: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("Test complete!")
print("=" * 80)
