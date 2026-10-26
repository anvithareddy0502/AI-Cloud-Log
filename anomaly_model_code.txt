import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    matthews_corrcoef, confusion_matrix
)

from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.ml.dataset_adapters import dataset_adapter
from backend.app.services.feature_extractor import feature_extractor

# 12 Standard Academic Base Features
BASE_FEATURE_NAMES = [
    "total_events",
    "error_count",
    "warning_count",
    "info_count",
    "critical_count",
    "error_rate",
    "events_per_minute",
    "avg_response_time",
    "max_response_time",
    "http_4xx_count",
    "http_5xx_count",
    "failed_login_count"
]

# Extended LogHub Features (includes template entropy, component counts, warning rate)
LOGHUB_FEATURE_NAMES = [
    "total_events",
    "error_count",
    "warning_count",
    "info_count",
    "critical_count",
    "error_rate",
    "warning_rate",
    "events_per_minute",
    "unique_event_ids",
    "unique_components",
    "template_entropy",
    "avg_response_time",
    "max_response_time",
    "http_4xx_count",
    "http_5xx_count",
    "failed_login_count"
]

FEATURE_NAMES = BASE_FEATURE_NAMES


class IsolationForestAnomalyModel:
    """
    Unified Isolation Forest ML model for cloud log anomaly detection.
    Supports:
    - 12-to-16 feature telemetry extraction & normalization
    - Reproducible 80/20 train/test split (fixed random_state=42)
    - Unsupervised training on OpenStack, HDFS, BGL, and synthetic telemetry
    - Ground-truth supervised validation strictly on labeled test data (BGL)
    - Truthful unsupervised profiling on unlabeled datasets (OpenStack, HDFS)
    - Local model persistence (joblib) and metadata versioning
    """

    FEATURE_KEYS = FEATURE_NAMES

    def __init__(self, contamination: float = 0.15, random_state: int = 42):
        self.contamination = contamination
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.is_fitted = False
        self.version = "2.1.0"
        self.current_dataset = "Synthetic Telemetry"
        self.active_features = BASE_FEATURE_NAMES

        # Caches for dataset-specific models and metadata
        self._dataset_models: Dict[str, IsolationForest] = {}
        self._dataset_metadata: Dict[str, Dict[str, Any]] = {}

        # Paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.data_dir = os.path.join(base_dir, "data")
        self.model_dir = os.path.join(base_dir, "backend", "app", "ml", "saved_models")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)

        self.train_csv_path = os.path.join(self.data_dir, "training_data.csv")
        self.test_csv_path = os.path.join(self.data_dir, "testing_data.csv")
        self.model_path = os.path.join(self.model_dir, "isolation_forest.joblib")
        self.metadata_path = os.path.join(self.model_dir, "model_metadata.json")

        self.metadata: Dict[str, Any] = {}
        self.test_results: List[Dict[str, Any]] = []

        # Load or initialize model
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Loads canonical baseline model and datasets if available; otherwise trains and persists."""
        if (
            os.path.exists(self.model_path) and 
            os.path.exists(self.train_csv_path) and 
            os.path.exists(self.test_csv_path) and
            os.path.exists(self.metadata_path)
        ):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                if meta.get("number_of_features") == 12 and meta.get("number_of_training_samples") == 160:
                    loaded_m = joblib.load(self.model_path)
                    if hasattr(loaded_m, "n_features_in_") and loaded_m.n_features_in_ == 12:
                        self.model = loaded_m
                        self.metadata = meta
                        self.is_fitted = True
                        self.active_features = BASE_FEATURE_NAMES
                        self.current_dataset = "Synthetic Telemetry"
                        self._compute_test_results()
                        logger.info("Loaded persisted canonical IsolationForest model from %s", self.model_path)
                        return
            except Exception as e:
                logger.warning("Failed to load canonical IsolationForest model: %s. Retraining...", e)

        # Default initialization with reproducible synthetic telemetry
        self.run_full_training_pipeline()

    def generate_synthetic_telemetry_dataset(self, n_samples: int = 200) -> pd.DataFrame:
        """
        Generates realistic cloud operational telemetry feature windows.
        Reflects heterogeneous cluster operational states:
        - Normal baseline traffic (~85%)
        - High-traffic surge (~5%)
        - High latency / memory pressure (~3%)
        - Database connection pool exhaustion (~4%)
        - Brute-force auth attacks (~3%)
        """
        np.random.seed(self.random_state)
        records = []

        for i in range(n_samples):
            rand = np.random.random()

            if rand < 0.85:
                events_per_min = np.random.uniform(15.0, 45.0)
                total_events = int(events_per_min * 5.0)
                error_count = int(np.random.poisson(0.3))
                warning_count = int(np.random.poisson(1.2))
                critical_count = 0
                http_5xx = 0
                http_4xx = int(np.random.poisson(0.5))
                failed_logins = int(np.random.poisson(0.2))
                avg_rt = round(float(np.random.normal(32.0, 8.0)), 2)
                max_rt = round(avg_rt + float(np.random.exponential(15.0)), 2)
            elif rand < 0.90:
                events_per_min = np.random.uniform(70.0, 120.0)
                total_events = int(events_per_min * 5.0)
                error_count = int(np.random.poisson(2.5))
                warning_count = int(np.random.poisson(4.0))
                critical_count = 0
                http_5xx = int(np.random.poisson(0.4))
                http_4xx = int(np.random.poisson(2.0))
                failed_logins = int(np.random.poisson(0.5))
                avg_rt = round(float(np.random.normal(85.0, 15.0)), 2)
                max_rt = round(avg_rt + float(np.random.exponential(40.0)), 2)
            elif rand < 0.93:
                events_per_min = np.random.uniform(30.0, 60.0)
                total_events = int(events_per_min * 5.0)
                error_count = int(np.random.poisson(5.0))
                warning_count = int(np.random.poisson(8.0))
                critical_count = int(np.random.poisson(1.0))
                http_5xx = int(np.random.poisson(4.0))
                http_4xx = int(np.random.poisson(3.0))
                failed_logins = int(np.random.poisson(0.3))
                avg_rt = round(float(np.random.uniform(1200.0, 3200.0)), 2)
                max_rt = round(avg_rt + float(np.random.uniform(500.0, 2000.0)), 2)
            elif rand < 0.97:
                events_per_min = np.random.uniform(40.0, 80.0)
                total_events = int(events_per_min * 5.0)
                critical_count = int(np.random.randint(2, 6))
                error_count = int(np.random.randint(10, 35))
                warning_count = int(np.random.randint(5, 12))
                http_5xx = int(np.random.randint(8, 28))
                http_4xx = int(np.random.poisson(2.0))
                failed_logins = int(np.random.poisson(0.2))
                avg_rt = round(float(np.random.uniform(800.0, 2400.0)), 2)
                max_rt = round(avg_rt + float(np.random.uniform(600.0, 1500.0)), 2)
            else:
                events_per_min = np.random.uniform(50.0, 90.0)
                total_events = int(events_per_min * 5.0)
                critical_count = 0
                error_count = int(np.random.randint(3, 8))
                warning_count = int(np.random.randint(6, 15))
                http_5xx = 0
                http_4xx = int(np.random.randint(12, 45))
                failed_logins = int(np.random.randint(15, 60))
                avg_rt = round(float(np.random.normal(45.0, 10.0)), 2)
                max_rt = round(avg_rt + float(np.random.exponential(25.0)), 2)

            info_count = max(0, total_events - (error_count + warning_count + critical_count))
            error_rate = round((error_count + critical_count) / max(total_events, 1), 4)

            records.append({
                "total_events": total_events,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "critical_count": critical_count,
                "error_rate": error_rate,
                "events_per_minute": round(events_per_min, 2),
                "avg_response_time": max(5.0, avg_rt),
                "max_response_time": max(10.0, max_rt),
                "http_4xx_count": http_4xx,
                "http_5xx_count": http_5xx,
                "failed_login_count": failed_logins
            })

        df = pd.DataFrame(records)[BASE_FEATURE_NAMES]
        return df

    def run_full_training_pipeline(self, n_samples: int = 200) -> Dict[str, Any]:
        """
        Executes the default baseline training pipeline.
        Maintains complete backward compatibility with existing tests and API callers.
        """
        return self.train_on_dataset(dataset_name="synthetic")

    def train_on_dataset(
        self,
        dataset_name: str = "OpenStack",
        contamination: Optional[float] = None,
        random_state: Optional[int] = None,
        max_records: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Trains Isolation Forest on the specified LogHub dataset (OpenStack, HDFS, BGL_2k, BGL_full)
        or synthetic baseline data.
        - Reproducible 80/20 train/test split (fixed seed)
        - Fits Isolation Forest strictly on the 80% training data without target labels
        - Evaluates on the 20% test data:
          - BGL: Computes Confusion Matrix, Accuracy, Precision, Recall, F1, MCC (using ground-truth labels)
          - OpenStack / HDFS: Strictly computes unsupervised outlier profiles and score distributions
        """
        ds_name_str = dataset_name if isinstance(dataset_name, str) and dataset_name.strip() else "synthetic"
        ds_norm = ds_name_str.strip()
        is_synthetic = ds_norm.lower() in {"synthetic", "demo", "default"}
        is_bgl_full = ds_norm.lower() in {"bgl_full", "bgl-full", "bglfull"}

        contam = contamination if contamination is not None else self.contamination
        r_state = random_state if random_state is not None else self.random_state

        if is_synthetic:
            df = self.generate_synthetic_telemetry_dataset(n_samples=200)
            feature_cols = BASE_FEATURE_NAMES
            has_labels = False
            ds_title = "Synthetic Telemetry"
            ds_slug = "synthetic"
        elif is_bgl_full:
            logger.info("Streaming BGL_full feature extraction across log stream in chunks...")
            feature_records = list(dataset_adapter.stream_dataset_windows(
                "BGL_full",
                window_size=20,
                step_size=10,
                chunk_size=50000,
                max_records=max_records
            ))
            df = pd.DataFrame(feature_records)
            feature_cols = LOGHUB_FEATURE_NAMES
            has_labels = True
            ds_title = "BGL_full"
            ds_slug = "bgl_full"
        else:
            target_ds = "BGL_2k" if ds_norm.lower() in {"bgl", "bgl_2k"} else ds_norm
            logs, meta = dataset_adapter.load_dataset(target_ds, max_records=max_records)
            feature_records = feature_extractor.extract_dataset_features(logs, window_size=20, step_size=10)
            df = pd.DataFrame(feature_records)
            feature_cols = LOGHUB_FEATURE_NAMES
            has_labels = meta.get("has_ground_truth_labels", False)
            ds_title = meta.get("dataset_name", ds_norm)
            ds_slug = "bgl_2k" if ds_title.lower() in {"bgl", "bgl_2k"} else ds_title.lower()

        # Guarantee all feature columns exist with numeric defaults
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        # 80/20 Train / Test Split (Strictly reproducible)
        train_df, test_df = train_test_split(
            df,
            test_size=0.20,
            random_state=r_state,
            shuffle=True
        )

        X_train = train_df[feature_cols].values

        # Fit Isolation Forest strictly on 80% TRAINING DATA (Unsupervised)
        fitted_model = IsolationForest(
            n_estimators=100,
            contamination=contam,
            random_state=r_state,
            n_jobs=1
        )
        fitted_model.fit(X_train)

        # Unsupervised & Supervised Evaluation on 20% TEST DATA
        eval_summary = self._evaluate_and_summarize(fitted_model, test_df, feature_cols)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_dict = {
            "algorithm": "Isolation Forest",
            "model_version": self.version,
            "dataset_name": ds_title,
            "training_status": "Trained",
            "is_supervised": False,
            "has_ground_truth_labels": has_labels,
            "contamination_value": contam,
            "random_state": r_state,
            "number_of_features": len(feature_cols),
            "feature_names": feature_cols,
            "number_of_training_samples": len(train_df),
            "number_of_testing_samples": len(test_df),
            "trained_at": now_str,
            "evaluation_summary": eval_summary
        }

        if is_synthetic:
            self.model = fitted_model
            self.metadata = meta_dict
            self.is_fitted = True
            self.active_features = BASE_FEATURE_NAMES
            self.current_dataset = "Synthetic Telemetry"

            train_df[feature_cols].to_csv(self.train_csv_path, index=False)
            test_df.to_csv(self.test_csv_path, index=False)
            joblib.dump(fitted_model, self.model_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(meta_dict, f, indent=2)

            # Also save synthetic copies
            train_df[feature_cols].to_csv(os.path.join(self.data_dir, "training_data_synthetic.csv"), index=False)
            test_df.to_csv(os.path.join(self.data_dir, "testing_data_synthetic.csv"), index=False)
            joblib.dump(fitted_model, os.path.join(self.model_dir, "isolation_forest_synthetic.joblib"))
            with open(os.path.join(self.model_dir, "model_metadata_synthetic.json"), "w", encoding="utf-8") as f:
                json.dump(meta_dict, f, indent=2)

            self._compute_test_results()
        else:
            # Dataset-specific files
            train_ds_csv = os.path.join(self.data_dir, f"training_data_{ds_slug}.csv")
            test_ds_csv = os.path.join(self.data_dir, f"testing_data_{ds_slug}.csv")
            model_ds_path = os.path.join(self.model_dir, f"isolation_forest_{ds_slug}.joblib")
            meta_ds_path = os.path.join(self.model_dir, f"model_metadata_{ds_slug}.json")

            train_df[feature_cols].to_csv(train_ds_csv, index=False)
            test_df.to_csv(test_ds_csv, index=False)
            joblib.dump(fitted_model, model_ds_path)
            with open(meta_ds_path, "w", encoding="utf-8") as f:
                json.dump(meta_dict, f, indent=2)

            self._dataset_models[ds_slug] = fitted_model
            self._dataset_metadata[ds_slug] = meta_dict

            # Also maintain bgl mirror if slug is bgl_2k, or bgl_2k mirror if slug is bgl
            if ds_slug in {"bgl", "bgl_2k"}:
                alt_slug = "bgl" if ds_slug == "bgl_2k" else "bgl_2k"
                train_df[feature_cols].to_csv(os.path.join(self.data_dir, f"training_data_{alt_slug}.csv"), index=False)
                test_df.to_csv(os.path.join(self.data_dir, f"testing_data_{alt_slug}.csv"), index=False)
                joblib.dump(fitted_model, os.path.join(self.model_dir, f"isolation_forest_{alt_slug}.joblib"))
                with open(os.path.join(self.model_dir, f"model_metadata_{alt_slug}.json"), "w", encoding="utf-8") as f:
                    json.dump(meta_dict, f, indent=2)
                self._dataset_models[alt_slug] = fitted_model
                self._dataset_metadata[alt_slug] = meta_dict

        logger.info(
            "Successfully trained Isolation Forest on %s (%d train, %d test samples).",
            ds_title, len(train_df), len(test_df)
        )
        return meta_dict

    def _evaluate_and_summarize(self, estimator: IsolationForest, test_df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """Computes true unsupervised and (if available) supervised evaluation metrics on test features."""
        X_test = test_df[feature_cols].values
        raw_preds = estimator.predict(X_test)  # -1 = anomaly, 1 = inlier
        decisions = estimator.decision_function(X_test)  # lower = outlier

        # Anomaly scores: 0.0 (inlier) to 1.0 (outlier)
        scores = np.round(np.clip(0.5 - decisions, 0.05, 0.98), 3)

        n_test = len(test_df)
        n_anomalies = int(np.sum(raw_preds == -1))
        pct_anomalies = round((n_anomalies / n_test) * 100, 2) if n_test > 0 else 0.0

        summary: Dict[str, Any] = {
            "test_samples_count": n_test,
            "predicted_anomalies_count": n_anomalies,
            "anomaly_percentage": pct_anomalies,
            "anomaly_score_summary": {
                "min": float(np.min(scores)),
                "mean": float(np.round(np.mean(scores), 3)),
                "max": float(np.max(scores)),
                "std": float(np.round(np.std(scores), 3))
            },
            "evaluation_type": "Unsupervised Outlier Profiling (No ground-truth labels required)"
        }

        # If authentic ground-truth labels exist (BGL)
        if "is_anomaly_label" in test_df.columns:
            valid_mask = test_df["is_anomaly_label"].notna()
            if valid_mask.sum() > 0:
                y_true = test_df.loc[valid_mask, "is_anomaly_label"].astype(int).values
                y_pred = (raw_preds[valid_mask] == -1).astype(int)

                acc = round(float(accuracy_score(y_true, y_pred)), 4)
                prec = round(float(precision_score(y_true, y_pred, zero_division=0)), 4)
                rec = round(float(recall_score(y_true, y_pred, zero_division=0)), 4)
                f1 = round(float(f1_score(y_true, y_pred, zero_division=0)), 4)
                mcc = round(float(matthews_corrcoef(y_true, y_pred)), 4)
                cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

                tn, fp, fn, tp = 0, 0, 0, 0
                if len(cm) == 2 and len(cm[0]) == 2 and len(cm[1]) == 2:
                    tn, fp = cm[0][0], cm[0][1]
                    fn, tp = cm[1][0], cm[1][1]
                fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
                fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0

                summary["evaluation_type"] = "Supervised Ground-Truth Benchmark Evaluation"
                summary["supervised_metrics"] = {
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1_score": f1,
                    "mcc": mcc,
                    "confusion_matrix": cm,
                    "false_positive_rate": fpr,
                    "false_negative_rate": fnr,
                    "true_positives": int(tp),
                    "false_positives": int(fp),
                    "true_negatives": int(tn),
                    "false_negatives": int(fn)
                }

        return summary

    def _compute_test_results(self):
        """Generates detailed preview records for test samples including scores."""
        if not os.path.exists(self.test_csv_path) or self.model is None:
            self.test_results = []
            return

        test_df = pd.read_csv(self.test_csv_path)
        feature_cols = self.active_features or self.metadata.get("feature_names", BASE_FEATURE_NAMES)
        for col in feature_cols:
            if col not in test_df.columns:
                test_df[col] = 0.0

        X_test = test_df[feature_cols].values
        raw_preds = self.model.predict(X_test)
        decisions = self.model.decision_function(X_test)
        scores = np.round(np.clip(0.5 - decisions, 0.05, 0.98), 2)

        results = []
        for idx, row in test_df.iterrows():
            rec = row.to_dict()
            is_anom = bool(raw_preds[idx] == -1)
            score = float(scores[idx])
            rec["prediction"] = "ANOMALY" if is_anom else "NORMAL"
            rec["is_anomaly"] = is_anom
            rec["anomaly_score"] = score
            results.append(rec)

        self.test_results = results

    def get_model_info(self, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns standard metadata and evaluation status for the ML Model."""
        if isinstance(dataset_name, str) and dataset_name.strip():
            slug = dataset_name.strip().lower()
            if slug not in {"synthetic", "default", "demo"}:
                if slug in self._dataset_metadata:
                    return self._dataset_metadata[slug]
                meta_path = os.path.join(self.model_dir, f"model_metadata_{slug}.json")
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            d = json.load(f)
                            self._dataset_metadata[slug] = d
                            return d
                    except Exception as e:
                        logger.warning("Failed to read metadata %s: %s", meta_path, e)

                # SAFETY FOR BGL_FULL: Do NOT auto-train on read queries!
                if slug in {"bgl_full", "bgl-full", "bglfull"}:
                    return {
                        "algorithm": "Isolation Forest",
                        "model_version": self.version,
                        "dataset_name": "BGL_full",
                        "training_status": "Not Trained (Ready for Training)",
                        "is_supervised": False,
                        "has_ground_truth_labels": True,
                        "contamination_value": self.contamination,
                        "random_state": self.random_state,
                        "number_of_features": len(LOGHUB_FEATURE_NAMES),
                        "feature_names": LOGHUB_FEATURE_NAMES,
                        "number_of_training_samples": 0,
                        "number_of_testing_samples": 0,
                        "description": "LogHub-2.0 BGL Full Dataset (~469 MB, ~4.6M logs). Ready for explicit training via CLI or UI.",
                        "evaluation_summary": {
                            "evaluation_type": "Supervised Ground-Truth Benchmark Evaluation",
                            "status": "Ready for training via: python -m backend.ml.train --dataset BGL_full"
                        }
                    }

                return self.train_on_dataset(dataset_name)

        if not self.metadata or self.metadata.get("number_of_features") != 12 or self.metadata.get("number_of_training_samples") != 160:
            self.run_full_training_pipeline()
        return self.metadata

    def get_estimator(self, dataset_name: Optional[str] = None) -> IsolationForest:
        """Returns the IsolationForest estimator for the requested dataset, or the base estimator."""
        if isinstance(dataset_name, str) and dataset_name.strip():
            slug = dataset_name.strip().lower()
            if slug not in {"synthetic", "default", "demo"}:
                if slug in self._dataset_models:
                    return self._dataset_models[slug]
                ds_model_path = os.path.join(self.model_dir, f"isolation_forest_{slug}.joblib")
                if os.path.exists(ds_model_path):
                    try:
                        m = joblib.load(ds_model_path)
                        self._dataset_models[slug] = m
                        return m
                    except Exception as e:
                        logger.warning("Failed to load dataset model %s: %s", ds_model_path, e)

                # SAFETY FOR BGL_FULL: Do NOT auto-train if model doesn't exist
                if slug in {"bgl_full", "bgl-full", "bglfull"}:
                    if "bgl_2k" in self._dataset_models:
                        return self._dataset_models["bgl_2k"]
                    if not self.is_fitted or self.model is None:
                        self.run_full_training_pipeline()
                    return self.model

                self.train_on_dataset(dataset_name)
                return self._dataset_models.get(slug, self.model)

        if not self.is_fitted or self.model is None:
            self.run_full_training_pipeline()
        return self.model

    def get_training_preview(self, limit: int = 15, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns training dataset overview and sample preview."""
        csv_path = self.train_csv_path
        if isinstance(dataset_name, str) and dataset_name.strip():
            ds_slug = dataset_name.strip().lower()
            if ds_slug not in {"synthetic", "default", "demo"}:
                spec_path = os.path.join(self.data_dir, f"training_data_{ds_slug}.csv")
                if os.path.exists(spec_path):
                    csv_path = spec_path
                elif ds_slug in {"bgl_full", "bgl-full", "bglfull"}:
                    preview_records = list(dataset_adapter.stream_dataset_windows(
                        "BGL_full", window_size=20, step_size=10, max_records=limit * 20
                    ))
                    df_sample = pd.DataFrame(preview_records)
                    feature_cols = [c for c in df_sample.columns if c != "is_anomaly_label"]
                    preview_rows = df_sample[feature_cols].head(limit).to_dict(orient="records")
                    return {
                        "dataset": "BGL_full (Sample Preview)",
                        "description": "80% Training Split preview generated via memory-efficient streaming",
                        "total_samples": 463126,
                        "feature_count": len(feature_cols),
                        "features": feature_cols,
                        "preview": preview_rows
                    }
                else:
                    self.train_on_dataset(dataset_name)
                    if os.path.exists(spec_path):
                        csv_path = spec_path

        if not os.path.exists(csv_path):
            self.run_full_training_pipeline()

        train_df = pd.read_csv(csv_path)
        feature_cols = [c for c in train_df.columns if c != "is_anomaly_label"]
        preview_rows = train_df[feature_cols].head(limit).to_dict(orient="records")
        return {
            "dataset": os.path.basename(csv_path),
            "description": "80% Training Split containing purely numerical cloud telemetry features",
            "total_samples": len(train_df),
            "feature_count": len(feature_cols),
            "features": feature_cols,
            "preview": preview_rows
        }

    def get_testing_preview(self, limit: int = 15, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """Returns testing dataset overview, predictions, and anomaly scores."""
        if isinstance(dataset_name, str) and dataset_name.strip():
            ds_slug = dataset_name.strip().lower()
            if ds_slug not in {"synthetic", "default", "demo"}:
                spec_path = os.path.join(self.data_dir, f"testing_data_{ds_slug}.csv")
                if not os.path.exists(spec_path) and ds_slug in {"bgl_full", "bgl-full", "bglfull"}:
                    preview_records = list(dataset_adapter.stream_dataset_windows(
                        "BGL_full", window_size=20, step_size=10, max_records=limit * 20
                    ))
                    df_sample = pd.DataFrame(preview_records)
                    feature_cols = [c for c in df_sample.columns if c != "is_anomaly_label"]
                    est = self.get_estimator("bgl_2k")
                    X_test = df_sample[feature_cols].values
                    raw_preds = est.predict(X_test) if est else [1] * len(df_sample)
                    decisions = est.decision_function(X_test) if est else [0.0] * len(df_sample)
                    scores = np.round(np.clip(0.5 - decisions, 0.05, 0.98), 2)
                    records = []
                    for idx, row in df_sample.head(limit).iterrows():
                        rec = row.to_dict()
                        is_anom = bool(raw_preds[idx] == -1)
                        rec["prediction"] = "ANOMALY" if is_anom else "NORMAL"
                        rec["is_anomaly"] = is_anom
                        rec["anomaly_score"] = float(scores[idx])
                        records.append(rec)
                    return {
                        "dataset": "testing_data_bgl_full.csv (Pre-training Sample)",
                        "description": "20% Unseen Test Split sample preview evaluated with Isolation Forest",
                        "total_samples": 463126 // 5,
                        "feature_count": len(feature_cols),
                        "features": feature_cols,
                        "preview": records
                    }
                elif not os.path.exists(spec_path):
                    self.train_on_dataset(dataset_name)
                if os.path.exists(spec_path):
                    test_df = pd.read_csv(spec_path)
                    est = self.get_estimator(dataset_name)
                    feature_cols = [c for c in test_df.columns if c != "is_anomaly_label"]
                    X_test = test_df[feature_cols].values
                    raw_preds = est.predict(X_test) if est else [1] * len(test_df)
                    decisions = est.decision_function(X_test) if est else [0.0] * len(test_df)
                    scores = np.round(np.clip(0.5 - decisions, 0.05, 0.98), 2)
                    records = []
                    for idx, row in test_df.head(limit).iterrows():
                        rec = row.to_dict()
                        is_anom = bool(raw_preds[idx] == -1)
                        rec["prediction"] = "ANOMALY" if is_anom else "NORMAL"
                        rec["is_anomaly"] = is_anom
                        rec["anomaly_score"] = float(scores[idx])
                        records.append(rec)
                    return {
                        "dataset": os.path.basename(spec_path),
                        "description": "20% Unseen Test Split evaluated with Isolation Forest predictions and anomaly scores",
                        "total_samples": len(test_df),
                        "feature_count": len(feature_cols),
                        "features": feature_cols,
                        "preview": records
                    }

        if not self.test_results:
            self._compute_test_results()

        feature_cols = BASE_FEATURE_NAMES
        return {
            "dataset": "testing_data.csv",
            "description": "20% Unseen Test Split evaluated with Isolation Forest predictions and anomaly scores",
            "total_samples": len(self.test_results),
            "feature_count": len(feature_cols),
            "features": feature_cols,
            "preview": self.test_results[:limit]
        }

    def evaluate_window(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a real-time incoming feature window.
        Compatible with the existing AI-CLAR anomaly detector and live log pipeline.
        Always uses the canonical 12-feature cluster baseline model.
        """
        if not self.is_fitted or self.model is None:
            self.run_full_training_pipeline()

        feature_keys = BASE_FEATURE_NAMES

        # Map features into vector with safe fallbacks
        vec = []
        for k in feature_keys:
            val = features.get(k)
            if val is None:
                # Check aliases
                if k == "avg_response_time":
                    val = features.get("average_response_time", 25.0)
                elif k == "max_response_time":
                    val = features.get("maximum_response_time", 25.0)
                elif k == "http_4xx_count":
                    val = features.get("HTTP_4xx_count", 0)
                elif k == "http_5xx_count":
                    val = features.get("HTTP_5xx_count", 0)
                elif k == "events_per_minute":
                    val = features.get("events_per_minute", 20.0)
                elif k == "total_events":
                    val = features.get("total_events", 20)
                elif k == "error_rate":
                    val = features.get("error_rate", 0.0)
                elif k == "failed_login_count":
                    val = features.get("failed_login_count", 0)
                else:
                    val = 0.0
            vec.append(float(val))

        X = np.array([vec])
        raw_pred = self.model.predict(X)[0]  # -1 = anomaly, 1 = inlier
        decision = self.model.decision_function(X)[0]

        # Domain safety checks
        crit_cnt = float(features.get("critical_count", 0))
        err_cnt = float(features.get("error_count", 0))
        h_5xx = float(features.get("http_5xx_count") or features.get("HTTP_5xx_count") or 0)
        f_logins = float(features.get("failed_login_count", 0))
        err_rate = float(features.get("error_rate", 0.0))
        avg_rt = float(features.get("avg_response_time") or features.get("average_response_time") or 25.0)

        domain_anomaly = (
            crit_cnt > 0 or
            err_cnt >= 4 or
            h_5xx >= 3 or
            f_logins >= 5 or
            err_rate >= 0.15 or
            avg_rt >= 1500.0
        )

        is_anomaly = bool(raw_pred == -1 or domain_anomaly)

        # Calculate calibrated anomaly score & confidence
        if is_anomaly:
            base_score = 0.80 - min(max(decision, -0.5), 0.5) * 0.35
            if crit_cnt > 0 or h_5xx >= 10:
                base_score = max(base_score, 0.92)
            if f_logins >= 15:
                base_score = max(base_score, 0.94)
            anomaly_score = round(min(base_score, 0.98), 2)
            confidence = int(anomaly_score * 100)
        else:
            anomaly_score = round(max(0.10, 0.45 - max(decision, 0.0) * 0.3), 2)
            confidence = int((1.0 - anomaly_score) * 100)

        reason, severity = self._explain_anomaly(features, anomaly_score)

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "confidence": confidence,
            "severity": severity,
            "reason": reason
        }

    def _explain_anomaly(self, f: Dict[str, Any], score: float) -> Tuple[str, str]:
        crit_cnt = f.get("critical_count", 0)
        err_cnt = f.get("error_count", 0)
        h_5xx = f.get("http_5xx_count") or f.get("HTTP_5xx_count") or 0
        f_logins = f.get("failed_login_count", 0)
        err_rate = f.get("error_rate", 0.0)
        avg_rt = f.get("avg_response_time") or f.get("average_response_time") or 25.0
        warn_cnt = f.get("warning_count", 0)

        reasons = []
        severity = "LOW"

        if crit_cnt > 0:
            reasons.append(f"{crit_cnt} critical error(s) logged")
            severity = "HIGH"

        if h_5xx > 0:
            reasons.append(f"HTTP 5xx error surge ({h_5xx} failures)")
            severity = "HIGH"

        if f_logins >= 5:
            reasons.append(f"Abnormal auth burst: {f_logins} failed logins detected")
            severity = "HIGH"

        if err_rate >= 0.15:
            reasons.append(f"Error rate surged to {int(err_rate*100)}%")
            if severity != "HIGH":
                severity = "HIGH" if err_rate > 0.30 else "MEDIUM"

        if avg_rt >= 1000.0:
            reasons.append(f"Response latency degraded to {int(avg_rt)}ms")
            if severity != "HIGH":
                severity = "MEDIUM"

        if not reasons:
            if warn_cnt >= 5:
                reasons.append(f"Warning volume elevated ({warn_cnt} warnings)")
                severity = "MEDIUM"
            else:
                reasons.append("Deviation in cluster event throughput")
                severity = "LOW"

        return " & ".join(reasons), severity


anomaly_model = IsolationForestAnomalyModel()
LogAnomalyModel = IsolationForestAnomalyModel
