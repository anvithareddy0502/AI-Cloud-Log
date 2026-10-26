"""
Bridge module for backward compatibility.
Re-exports the unified IsolationForestAnomalyModel from backend.app.services.anomaly_model.
"""
from backend.app.services.anomaly_model import (
    anomaly_model,
    IsolationForestAnomalyModel,
    LogAnomalyModel,
    FEATURE_NAMES
)

__all__ = [
    "anomaly_model",
    "IsolationForestAnomalyModel",
    "LogAnomalyModel",
    "FEATURE_NAMES"
]
