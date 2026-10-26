import os
import json
import joblib
import pandas as pd
import pytest
from sklearn.ensemble import IsolationForest

from backend.app.services.feature_extractor import feature_extractor
from backend.app.services.anomaly_model import anomaly_model, FEATURE_NAMES, IsolationForestAnomalyModel
from backend.app.routes.ml import get_ml_model_info, get_training_data, get_testing_data, retrain_model

def test_12_feature_extraction():
    """
    Verifies that feature_extractor extracts all 12 requested academic numerical features
    and preserves backward-compatible legacy keys.
    """
    sample_logs = [
        {"timestamp": "2026-09-08 10:00:00", "severity": "INFO", "status_code": 200, "response_time_ms": 30.0, "message": "GET /api/v1/health 200 OK"},
        {"timestamp": "2026-09-08 10:01:00", "severity": "WARNING", "status_code": 404, "response_time_ms": 45.0, "message": "GET /favicon.ico 404 Not Found"},
        {"timestamp": "2026-09-08 10:02:00", "severity": "ERROR", "status_code": 500, "response_time_ms": 850.0, "message": "Internal Server Error in database driver"},
        {"timestamp": "2026-09-08 10:03:00", "severity": "CRITICAL", "status_code": 503, "response_time_ms": 1200.0, "message": "Service unavailable: connection timeout"},
        {"timestamp": "2026-09-08 10:04:00", "severity": "ERROR", "status_code": 401, "response_time_ms": 25.0, "message": "Authentication failed for admin: bad credentials"}
    ]

    feature_windows = feature_extractor.extract_features(sample_logs)
    assert len(feature_windows) > 0
    features = feature_windows[0]

    # All 12 features must be present
    for feature in FEATURE_NAMES:
        assert feature in features, f"Feature '{feature}' missing from feature_extractor output"

    assert features["total_events"] == 5
    assert features["error_count"] == 2
    assert features["warning_count"] == 1
    assert features["info_count"] == 1
    assert features["critical_count"] == 1
    assert features["http_4xx_count"] == 2  # 404 and 401
    assert features["http_5xx_count"] == 2  # 500 and 503
    assert features["failed_login_count"] == 1  # 401 auth failure
    assert features["avg_response_time"] > 0
    assert features["max_response_time"] == 1200.0
    assert features["error_rate"] == 0.6  # (2 errors + 1 critical) / 5

    # Backward compatibility aliases
    assert "average_response_time" in features
    assert "maximum_response_time" in features
    assert "HTTP_4xx_count" in features
    assert "HTTP_5xx_count" in features

def test_training_and_testing_data_split_integrity():
    """
    Verifies 80/20 train/test split and strict unsupervised structure.
    No artificial class labels or fake target columns are allowed in training data.
    """
    train_path = anomaly_model.train_csv_path
    test_path = anomaly_model.test_csv_path

    assert os.path.exists(train_path), "training_data.csv must exist"
    assert os.path.exists(test_path), "testing_data.csv must exist"

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    # Verify 80/20 split on 200 samples
    assert len(train_df) == 160, f"Expected 160 training samples (80%), got {len(train_df)}"
    assert len(test_df) == 40, f"Expected 40 testing samples (20%), got {len(test_df)}"

    # Verify exact feature columns in training data
    assert list(train_df.columns) == FEATURE_NAMES, "training_data.csv columns must match standard 12 features"
    assert list(test_df.columns) == FEATURE_NAMES, "testing_data.csv columns must match standard 12 features"

    # Strict unsupervised check: NO target labels
    for forbidden_col in ["label", "is_anomaly", "target", "class", "y", "ground_truth"]:
        assert forbidden_col not in train_df.columns, (
            f"Academic integrity violation: '{forbidden_col}' found in training_data.csv. "
            "Isolation Forest is unsupervised and training data must not have labels!"
        )

def test_isolation_forest_model_and_unsupervised_evaluation():
    """
    Verifies Isolation Forest fitting, outlier prediction (-1/1), normalized scoring,
    and genuine unsupervised evaluation metrics without fabricated accuracy.
    """
    assert anomaly_model.is_fitted is True
    assert isinstance(anomaly_model.model, IsolationForest)

    info = anomaly_model.get_model_info()
    assert info["algorithm"] == "Isolation Forest"
    assert info["is_supervised"] is False
    assert info["number_of_features"] == 12
    assert info["number_of_training_samples"] == 160
    assert info["number_of_testing_samples"] == 40

    eval_summary = info.get("evaluation_summary", {})
    assert eval_summary["test_samples_count"] == 40
    assert eval_summary["predicted_anomalies_count"] >= 0
    assert 0.0 <= eval_summary["anomaly_percentage"] <= 100.0

    score_dist = eval_summary["anomaly_score_summary"]
    assert 0.0 <= score_dist["min"] <= 1.0
    assert 0.0 <= score_dist["mean"] <= 1.0
    assert 0.0 <= score_dist["max"] <= 1.0
    assert score_dist["max"] >= score_dist["min"]
    assert score_dist["std"] >= 0.0

    # Ensure no fabricated supervised metrics exist
    for fake_metric in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
        assert fake_metric not in eval_summary, f"Fabricated metric '{fake_metric}' should not be in unsupervised evaluation"

def test_model_persistence_and_reload():
    """
    Verifies that the trained model is saved with joblib and loads correctly.
    """
    model_path = anomaly_model.model_path
    metadata_path = anomaly_model.metadata_path

    assert os.path.exists(model_path), f"Joblib model file missing at {model_path}"
    assert os.path.exists(metadata_path), f"Metadata file missing at {metadata_path}"
    assert os.path.getsize(model_path) > 1000, "Joblib model file is abnormally small"

    loaded_estimator = joblib.load(model_path)
    assert isinstance(loaded_estimator, IsolationForest)

    # Test predicting on a known normal vector
    normal_vector = [[150, 0, 1, 149, 0, 0.0, 30.0, 25.0, 40.0, 0, 0, 0]]
    pred = loaded_estimator.predict(normal_vector)[0]
    assert pred in [-1, 1]

def test_real_time_window_evaluation():
    """
    Verifies evaluate_window() for normal vs anomalous cluster windows.
    """
    normal_window = {
        "total_events": 150,
        "error_count": 0,
        "warning_count": 1,
        "info_count": 149,
        "critical_count": 0,
        "error_rate": 0.0,
        "events_per_minute": 30.0,
        "avg_response_time": 28.5,
        "max_response_time": 50.0,
        "http_4xx_count": 0,
        "http_5xx_count": 0,
        "failed_login_count": 0
    }
    normal_res = anomaly_model.evaluate_window(normal_window)
    assert normal_res["is_anomaly"] is False
    assert normal_res["anomaly_score"] < 0.60

    critical_window = {
        "total_events": 200,
        "error_count": 35,
        "warning_count": 10,
        "info_count": 140,
        "critical_count": 5,
        "error_rate": 0.20,
        "events_per_minute": 40.0,
        "avg_response_time": 1850.0,
        "max_response_time": 4200.0,
        "http_4xx_count": 2,
        "http_5xx_count": 28,
        "failed_login_count": 0
    }
    anom_res = anomaly_model.evaluate_window(critical_window)
    assert anom_res["is_anomaly"] is True
    assert anom_res["severity"] == "HIGH"
    assert anom_res["anomaly_score"] >= 0.80
    assert "critical error" in anom_res["reason"].lower() or "5xx" in anom_res["reason"].lower()

def test_ml_api_route_handlers():
    """
    Verifies the ML route handler functions directly.
    """
    # 1. get_ml_model_info
    info_res = get_ml_model_info()
    assert info_res["status"] == "success"
    assert info_res["model_info"]["algorithm"] == "Isolation Forest"
    assert "academic_notes" in info_res

    # 2. get_training_data
    train_res = get_training_data(limit=10, offset=0)
    assert train_res["status"] == "success"
    assert train_res["total_samples"] == 160
    assert len(train_res["samples"]) == 10
    assert train_res["has_target_labels"] is False
    assert list(train_res["samples"][0].keys()) == FEATURE_NAMES

    # 3. get_testing_data
    test_res = get_testing_data(limit=5, offset=0)
    assert test_res["status"] == "success"
    assert test_res["total_samples"] == 40
    assert len(test_res["samples"]) == 5
    assert "prediction" in test_res["samples"][0]
    assert "anomaly_score" in test_res["samples"][0]
    assert test_res["predicted_anomalies_count"] >= 0
