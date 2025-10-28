"""MLflow tracing and feedback module for model evaluation."""

import os
import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType
from typing import Optional
from .config import DatabricksConfig


def setup_mlflow(config: DatabricksConfig):
    """Set up MLflow tracking with Databricks."""
    # Use environment variable if set, otherwise default to databricks://aws
    if "MLFLOW_TRACKING_URI" in os.environ:
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    else:
        mlflow.set_tracking_uri("databricks://aws")
    # Set experiment by name
    mlflow.set_experiment(experiment_name=config.experiment_name)


def get_most_recent_trace_id(config: DatabricksConfig) -> Optional[str]:
    """
    Get the most recent trace ID from the MLflow experiment.

    Args:
        config: Databricks configuration

    Returns:
        The most recent trace request_id, or None if no traces found
    """
    try:
        experiment = mlflow.get_experiment_by_name(config.experiment_name)
        if not experiment:
            print(f"⚠️ Experiment not found: {config.experiment_name}")
            return None

        # Search for most recent trace
        traces = mlflow.search_traces(
            experiment_ids=[experiment.experiment_id], max_results=1, order_by=["timestamp_ms DESC"]
        )

        if traces is not None and not traces.empty:
            # traces is a DataFrame, get the first row
            trace_row = traces.iloc[0]
            trace_id = trace_row.get("request_id")
            print(f"✅ Found most recent trace: {trace_id}")
            return trace_id
        else:
            print("⚠️ No traces found in experiment")
            return None

    except Exception as e:
        print(f"❌ Error getting most recent trace: {e}")
        import traceback

        traceback.print_exc()
        return None


def log_user_satisfaction(
    trace_id: str,
    satisfied: bool,
    user_id: str,
    message_id: Optional[int] = None,
    use_mlflow: bool = True,
):
    """
    Log user satisfaction feedback (thumbs up/down) to MLflow only.

    Args:
        trace_id: Trace ID from MLflow
        satisfied: True for thumbs up, False for thumbs down
        user_id: User email or identifier
        message_id: Optional message ID (not used, kept for compatibility)
        use_mlflow: If True, log to MLflow
    """
    try:
        if use_mlflow:
            mlflow.log_feedback(
                trace_id=trace_id,
                name="user_satisfaction",
                value=satisfied,
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"✅ Satisfaction feedback logged to MLflow for trace {trace_id}")
            return True
        else:
            print(f"⚠️ MLflow logging disabled, feedback not saved")
            return False
    except Exception as e:
        print(f"❌ Error logging satisfaction feedback: {e}")
        import traceback

        traceback.print_exc()
        return False


def log_review_request(
    trace_id: str,
    user_id: str,
    message_id: Optional[int] = None,
    use_mlflow: bool = True,
):
    """
    Log that a response was flagged for review to MLflow only.

    Args:
        trace_id: Trace ID from MLflow
        user_id: User email or identifier
        message_id: Optional message ID (not used, kept for compatibility)
        use_mlflow: If True, log to MLflow
    """
    try:
        if use_mlflow:
            mlflow.log_feedback(
                trace_id=trace_id,
                name="flagged_for_review",
                value=True,
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"✅ Review request logged to MLflow for trace {trace_id}")
            return True
        else:
            print(f"⚠️ MLflow logging disabled, feedback not saved")
            return False
    except Exception as e:
        print(f"❌ Error logging review request: {e}")
        import traceback

        traceback.print_exc()
        return False


def log_correction(
    trace_id: str,
    correction_text: str,
    user_id: str,
    message_id: Optional[int] = None,
    use_mlflow: bool = True,
):
    """
    Log a correction or expected output for a response to MLflow only.

    Args:
        trace_id: Trace ID from MLflow
        correction_text: The correction or expected output
        user_id: User email or identifier
        message_id: Optional message ID (not used, kept for compatibility)
        use_mlflow: If True, log to MLflow
    """
    try:
        if use_mlflow:
            mlflow.log_expectation(
                trace_id=trace_id,
                name="user_correction",
                value=[correction_text],
                source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id=user_id),
            )
            print(f"✅ Correction logged to MLflow for trace {trace_id}")
            return True
        else:
            print(f"⚠️ MLflow logging disabled, feedback not saved")
            return False
    except Exception as e:
        print(f"❌ Error logging correction: {e}")
        import traceback

        traceback.print_exc()
        return False
