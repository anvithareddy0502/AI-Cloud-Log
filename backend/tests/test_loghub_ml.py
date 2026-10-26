"""
Test Suite for LogHub Dataset Adapters, Feature Extraction, Isolation Forest Training,
and Baseline Research Evaluation.
"""
import os
import subprocess
import pytest
from backend.app.ml.dataset_adapters import dataset_adapter
from backend.app.services.feature_extractor import feature_extractor
from backend.app.services.anomaly_model import anomaly_model
from backend.app.ml.baselines import evaluate_baselines


def test_dataset_adapters_openstack():
    logs, meta = dataset_adapter.load_dataset("OpenStack")
    assert len(logs) == 2000
    assert meta["has_ground_truth_labels"] is False
    assert logs[0]["dataset"] == "OpenStack"
    assert "timestamp" in logs[0]
    assert "server" in logs[0]
    assert "service" in logs[0]


def test_dataset_adapters_hdfs():
    logs, meta = dataset_adapter.load_dataset("HDFS")
    assert len(logs) == 2000
    assert meta["has_ground_truth_labels"] is False
    assert logs[0]["dataset"] == "HDFS"
    assert logs[0]["timestamp"].startswith("2008-11-09")


def test_dataset_adapters_bgl():
    logs, meta = dataset_adapter.load_dataset("BGL")
    assert len(logs) == 2000
    assert meta["has_ground_truth_labels"] is True
    assert meta["labeled_anomaly_count"] == 143
    assert logs[0]["dataset"] == "BGL"
    # First entry in BGL has Label = '-' (normal)
    assert logs[0]["is_anomaly_label"] == 0
    # Search for known anomaly entry
    anom_logs = [l for l in logs if l["is_anomaly_label"] == 1]
    assert len(anom_logs) == 143


def test_dataset_feature_extraction():
    logs, _ = dataset_adapter.load_dataset("OpenStack")
    windows = feature_extractor.extract_dataset_features(logs, window_size=20, step_size=10)
    assert len(windows) == 199
    w0 = windows[0]
    assert w0["total_events"] == 20
    assert "unique_event_ids" in w0
    assert "template_entropy" in w0
    assert "warning_rate" in w0
    assert "events_per_minute" in w0


def test_isolation_forest_multi_dataset_training():
    for ds in ["OpenStack", "HDFS", "BGL"]:
        meta = anomaly_model.train_on_dataset(ds, contamination=0.15, random_state=42)
        assert meta["training_status"] == "Trained"
        assert meta["number_of_training_samples"] == 159
        assert meta["number_of_testing_samples"] == 40
        assert meta["number_of_features"] == 16
        eval_sum = meta["evaluation_summary"]
        assert eval_sum["test_samples_count"] == 40
        assert eval_sum["predicted_anomalies_count"] >= 0


def test_bgl_supervised_metrics_calculation():
    meta = anomaly_model.train_on_dataset("BGL", contamination=0.15, random_state=42)
    eval_sum = meta["evaluation_summary"]
    assert "supervised_metrics" in eval_sum
    sm = eval_sum["supervised_metrics"]
    assert 0.0 <= sm["accuracy"] <= 1.0
    assert 0.0 <= sm["precision"] <= 1.0
    assert 0.0 <= sm["recall"] <= 1.0
    assert 0.0 <= sm["f1_score"] <= 1.0
    assert -1.0 <= sm["mcc"] <= 1.0
    assert len(sm["confusion_matrix"]) == 2


def test_unlabeled_datasets_omit_fake_metrics():
    for ds in ["OpenStack", "HDFS"]:
        meta = anomaly_model.train_on_dataset(ds, contamination=0.15, random_state=42)
        eval_sum = meta["evaluation_summary"]
        assert "supervised_metrics" not in eval_sum or eval_sum.get("supervised_metrics") is None
        assert "accuracy" not in eval_sum
        assert "precision" not in eval_sum
        assert "recall" not in eval_sum
        assert "f1_score" not in eval_sum


def test_baseline_models_comparison():
    bgl_res = evaluate_baselines("BGL", random_state=42)
    models = bgl_res["models"]
    assert "Isolation Forest" in models
    assert "One-Class SVM" in models
    assert "Local Outlier Factor" in models
    assert "Random Forest" in models
    assert "Logistic Regression" in models
    assert "SVM" in models

    # Check that Random Forest and Isolation Forest have valid test metrics
    assert "f1_score" in models["Isolation Forest"]
    assert "f1_score" in models["Random Forest"]


def test_cli_commands_execution():
    cmd_train = [
        os.path.join(".", "backend", ".venv", "Scripts", "python.exe"),
        "-m", "backend.ml.train", "--dataset", "OpenStack"
    ]
    res_train = subprocess.run(cmd_train, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH="."))
    assert res_train.returncode == 0
    assert "Model training completed and persisted successfully" in res_train.stdout

    cmd_eval = [
        os.path.join(".", "backend", ".venv", "Scripts", "python.exe"),
        "-m", "backend.ml.evaluate", "--dataset", "BGL"
    ]
    res_eval = subprocess.run(cmd_eval, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH="."))
    assert res_eval.returncode == 0
    assert "Ground-Truth Benchmark Metrics" in res_eval.stdout
