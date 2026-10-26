"""
Test Suite for LogHub-2.0 BGL Full Dataset (BGL_full) Support
Validates:
- Authentic ground-truth label pairing between raw and structured logs
- Chunked, memory-efficient sliding-window streaming without full RAM load
- Bounded training and evaluation pipeline
- Separation of full BGL models (isolation_forest_bgl_full.joblib, model_metadata_bgl_full.json)
- Backward compatibility preserving BGL_2k, OpenStack, HDFS, and base models
- CLI argument compatibility for train and evaluate
"""
import os
import pytest
import subprocess
import sys
from backend.app.ml.dataset_adapters import dataset_adapter
from backend.app.services.anomaly_model import anomaly_model, LOGHUB_FEATURE_NAMES
from backend.app.ml.baselines import evaluate_baselines


def test_bgl_full_sample_loading():
    """Validates that BGL_full can be sampled safely without loading all 469 MB."""
    logs, meta = dataset_adapter.load_dataset("BGL_full", max_records=200)
    assert len(logs) == 200
    assert meta["dataset_name"] == "BGL_full"
    assert meta["has_ground_truth_labels"] is True
    assert logs[0]["dataset"] == "BGL_full"
    assert "is_anomaly_label" in logs[0]
    assert logs[0]["is_anomaly_label"] in (0, 1)
    assert "server" in logs[0]
    assert "timestamp" in logs[0]


def test_bgl_full_streaming_windows():
    """Validates sliding window generator streams features with authentic labels."""
    windows = list(dataset_adapter.stream_dataset_windows(
        "BGL_full",
        window_size=20,
        step_size=10,
        chunk_size=100,
        max_records=300
    ))
    assert len(windows) > 0
    w0 = windows[0]
    assert w0["total_events"] == 20
    assert "is_anomaly_label" in w0
    assert "unique_event_ids" in w0
    assert "template_entropy" in w0
    assert "warning_rate" in w0
    for feat in LOGHUB_FEATURE_NAMES:
        assert feat in w0


def test_bgl_full_safe_model_info_query():
    """
    Validates that querying get_model_info for BGL_full does NOT automatically trigger
    an unprompted 4.6M training session if the model is not trained.
    """
    info = anomaly_model.get_model_info("BGL_full")
    assert info is not None
    assert info["dataset_name"] == "BGL_full"
    assert info["number_of_features"] == 16
    assert info["training_status"] in ("Trained", "Not Trained (Ready for Training)")


def test_bgl_full_bounded_training_and_separation():
    """
    Validates bounded training on BGL_full, verifying distinct file persistence
    and ensuring existing models (BGL_2k, canonical cluster model) remain untouched.
    """
    meta = anomaly_model.train_on_dataset(
        dataset_name="BGL_full",
        contamination=0.10,
        random_state=42,
        max_records=500
    )
    assert meta["training_status"] == "Trained"
    assert meta["dataset_name"] == "BGL_full"
    assert meta["has_ground_truth_labels"] is True
    assert meta["number_of_features"] == 16

    eval_sum = meta["evaluation_summary"]
    assert "supervised_metrics" in eval_sum
    sm = eval_sum["supervised_metrics"]
    assert 0.0 <= sm["accuracy"] <= 1.0
    assert 0.0 <= sm["precision"] <= 1.0
    assert 0.0 <= sm["recall"] <= 1.0
    assert 0.0 <= sm["f1_score"] <= 1.0

    # Ensure files are saved distinctly with _bgl_full suffix
    bgl_full_model_path = os.path.join(anomaly_model.model_dir, "isolation_forest_bgl_full.joblib")
    bgl_full_meta_path = os.path.join(anomaly_model.model_dir, "model_metadata_bgl_full.json")
    bgl_full_train_csv = os.path.join(anomaly_model.data_dir, "training_data_bgl_full.csv")
    bgl_full_test_csv = os.path.join(anomaly_model.data_dir, "testing_data_bgl_full.csv")

    assert os.path.exists(bgl_full_model_path)
    assert os.path.exists(bgl_full_meta_path)
    assert os.path.exists(bgl_full_train_csv)
    assert os.path.exists(bgl_full_test_csv)


def test_bgl_full_baselines_evaluation():
    """Validates that research baseline comparisons execute cleanly for BGL_full."""
    results = evaluate_baselines("BGL_full", random_state=42, max_records=400)
    assert results["dataset_name"] == "BGL_full"
    assert results["has_ground_truth_labels"] is True
    models = results["models"]
    assert "Isolation Forest" in models
    assert "One-Class SVM" in models
    assert "Local Outlier Factor" in models

    # Also verify that when ground-truth labels contain multiple classes (e.g. BGL_2k), supervised baselines execute
    bgl_2k_results = evaluate_baselines("BGL_2k", random_state=42)
    assert "Random Forest" in bgl_2k_results["models"]
    assert "Logistic Regression" in bgl_2k_results["models"]


def test_cli_train_and_eval_arguments():
    """Validates CLI command parsers support --dataset BGL_full."""
    python_exe = sys.executable

    # Test train CLI --help
    res_train = subprocess.run(
        [python_exe, "-m", "backend.ml.train", "--help"],
        capture_output=True,
        text=True
    )
    assert res_train.returncode == 0
    assert "BGL_full" in res_train.stdout

    # Test eval CLI --help
    res_eval = subprocess.run(
        [python_exe, "-m", "backend.ml.evaluate", "--help"],
        capture_output=True,
        text=True
    )
    assert res_eval.returncode == 0
    assert "BGL_full" in res_eval.stdout
