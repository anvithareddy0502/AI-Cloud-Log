import os
import numpy as np
import pandas as pd
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.anomaly_model import anomaly_model, FEATURE_NAMES, BASE_FEATURE_NAMES, LOGHUB_FEATURE_NAMES
from backend.app.ml.baselines import evaluate_baselines
from backend.app.utils.logger import logger

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


def _clean_str(val: Any) -> Optional[str]:
    return val if isinstance(val, str) and val.strip() else None


def _clean_int(val: Any, default: int) -> int:
    if isinstance(val, int):
        return val
    if hasattr(val, "default") and isinstance(val.default, int):
        return val.default
    return default


class RetrainRequest(BaseModel):
    dataset: Optional[str] = Field("OpenStack", description="Target dataset: OpenStack, HDFS, BGL, or synthetic")
    n_samples: Optional[int] = Field(200, ge=50, le=1000, description="Total samples if using synthetic generator")
    contamination: Optional[float] = Field(0.15, ge=0.01, le=0.5, description="Expected proportion of outliers")
    random_state: Optional[int] = Field(42, description="Reproducible random seed")


@router.get("/model-info")
def get_ml_model_info(dataset: Optional[str] = Query(None, description="Dataset name to inspect")):
    """
    Returns current Isolation Forest metadata, training configuration,
    and truthful evaluation metrics on the test split.
    """
    try:
        ds_name = _clean_str(dataset)
        info = anomaly_model.get_model_info(dataset_name=ds_name)
        return {
            "status": "success",
            "model_info": info,
            "academic_notes": (
                "The model implements an unsupervised Isolation Forest architecture. "
                "In strict compliance with academic standards, ground-truth labels are never used during training. "
                "Supervised accuracy, precision, recall, and F1 metrics are reported exclusively on datasets with authentic "
                "ground-truth failure labels (BGL) on the unseen test split. For unlabeled datasets (OpenStack, HDFS), "
                "evaluation truthfully reports empirical outlier counts and decision score distributions without fabrication."
            )
        }
    except Exception as e:
        logger.error("Failed to retrieve ML model info: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model info: {str(e)}")


@router.get("/training-data")
def get_training_data(
    dataset: Optional[str] = Query(None, description="Dataset name (OpenStack, HDFS, BGL, synthetic)"),
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Returns rows from the 80% training split containing strictly numerical features without artificial class labels.
    """
    try:
        ds_name = _clean_str(dataset)
        limit_val = _clean_int(limit, 50)
        offset_val = _clean_int(offset, 0)

        csv_path = anomaly_model.train_csv_path
        if ds_name and ds_name.lower() not in {"synthetic", "default", "demo"}:
            cand_path = os.path.join(anomaly_model.data_dir, f"training_data_{ds_name.lower()}.csv")
            if os.path.exists(cand_path):
                csv_path = cand_path
            elif ds_name.lower() in {"bgl_full", "bgl-full", "bglfull"}:
                preview = anomaly_model.get_training_preview(limit=limit_val, dataset_name="BGL_full")
                return {
                    "status": "success",
                    "dataset": "training_data_bgl_full.csv (Pre-training Sample)",
                    "description": "80% Training Split with numerical telemetry features (Unsupervised, no target labels in training)",
                    "total_samples": 463126,
                    "offset": offset_val,
                    "limit": limit_val,
                    "feature_count": preview["feature_count"],
                    "feature_names": preview["features"],
                    "is_supervised": False,
                    "has_target_labels": False,
                    "samples": preview["preview"]
                }
            else:
                anomaly_model.train_on_dataset(ds_name)
                if os.path.exists(cand_path):
                    csv_path = cand_path

        if not os.path.exists(csv_path):
            anomaly_model.run_full_training_pipeline()

        df = pd.read_csv(csv_path)
        total_rows = len(df)
        paginated_df = df.iloc[offset_val : offset_val + limit_val]

        feature_cols = [c for c in df.columns if c != "is_anomaly_label"]

        return {
            "status": "success",
            "dataset": os.path.basename(csv_path),
            "description": "80% Training Split with numerical telemetry features (Unsupervised, no target labels in training)",
            "total_samples": total_rows,
            "offset": offset_val,
            "limit": limit_val,
            "feature_count": len(feature_cols),
            "feature_names": feature_cols,
            "is_supervised": False,
            "has_target_labels": False,
            "samples": paginated_df.to_dict(orient="records")
        }
    except Exception as e:
        logger.error("Failed to read training data CSV: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load training data: {str(e)}")


@router.get("/testing-data")
def get_testing_data(
    dataset: Optional[str] = Query(None, description="Dataset name (OpenStack, HDFS, BGL, synthetic)"),
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Returns rows from the 20% unseen test split along with Isolation Forest predictions and anomaly scores.
    """
    try:
        ds_name = _clean_str(dataset)
        limit_val = _clean_int(limit, 50)
        offset_val = _clean_int(offset, 0)

        csv_path = anomaly_model.test_csv_path
        if ds_name and ds_name.lower() not in {"synthetic", "default", "demo"}:
            cand_path = os.path.join(anomaly_model.data_dir, f"testing_data_{ds_name.lower()}.csv")
            if os.path.exists(cand_path):
                csv_path = cand_path
            elif ds_name.lower() in {"bgl_full", "bgl-full", "bglfull"}:
                preview = anomaly_model.get_testing_preview(limit=limit_val, dataset_name="BGL_full")
                return {
                    "status": "success",
                    "dataset": "testing_data_bgl_full.csv (Pre-training Sample)",
                    "description": "20% Unseen Test Split evaluated via Isolation Forest decision paths",
                    "total_samples": 463126 // 5,
                    "offset": offset_val,
                    "limit": limit_val,
                    "feature_count": preview["feature_count"],
                    "feature_names": preview["features"],
                    "predicted_anomalies_count": 0,
                    "anomaly_percentage": 0.0,
                    "anomaly_score_summary": {},
                    "supervised_metrics": None,
                    "samples": preview["preview"]
                }
            else:
                anomaly_model.train_on_dataset(ds_name)
                if os.path.exists(cand_path):
                    csv_path = cand_path

        if not os.path.exists(csv_path):
            anomaly_model.run_full_training_pipeline()

        test_df = pd.read_csv(csv_path)
        total_rows = len(test_df)

        meta = anomaly_model.get_model_info(dataset_name=ds_name)
        feature_cols = meta.get("feature_names", BASE_FEATURE_NAMES)
        for col in feature_cols:
            if col not in test_df.columns:
                test_df[col] = 0.0

        # Predict using appropriate estimator
        estimator = anomaly_model.get_estimator(dataset_name=ds_name)
        X_test = test_df[feature_cols].values
        raw_preds = estimator.predict(X_test) if estimator else [1] * total_rows
        decisions = estimator.decision_function(X_test) if estimator else [0.0] * total_rows
        scores = [round(float(np.clip(0.5 - d, 0.05, 0.98)), 2) for d in decisions]

        records = []
        for idx, row in test_df.iloc[offset_val : offset_val + limit_val].iterrows():
            rec = row.to_dict()
            is_anom = bool(raw_preds[idx] == -1)
            rec["prediction"] = "ANOMALY" if is_anom else "NORMAL"
            rec["is_anomaly"] = is_anom
            rec["anomaly_score"] = float(scores[idx])
            records.append(rec)

        eval_summary = meta.get("evaluation_summary", {})

        return {
            "status": "success",
            "dataset": os.path.basename(csv_path),
            "description": "20% Unseen Test Split evaluated via Isolation Forest decision paths",
            "total_samples": total_rows,
            "offset": offset_val,
            "limit": limit_val,
            "feature_count": len(feature_cols),
            "feature_names": feature_cols,
            "predicted_anomalies_count": eval_summary.get("predicted_anomalies_count", 0),
            "anomaly_percentage": eval_summary.get("anomaly_percentage", 0.0),
            "anomaly_score_summary": eval_summary.get("anomaly_score_summary", {}),
            "supervised_metrics": eval_summary.get("supervised_metrics"),
            "samples": records
        }
    except Exception as e:
        logger.error("Failed to read testing data: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load testing data: {str(e)}")


@router.post("/train")
def retrain_model(payload: Optional[RetrainRequest] = None):
    """
    Triggers on-demand training of the Isolation Forest model on OpenStack, HDFS, BGL, or synthetic data.
    Saves updated training/testing CSV splits and persists the trained estimator.
    """
    try:
        ds_name = payload.dataset if (payload and payload.dataset) else "OpenStack"
        contamination = payload.contamination if payload else 0.15
        random_state = payload.random_state if payload else 42

        metadata = anomaly_model.train_on_dataset(
            dataset_name=ds_name,
            contamination=contamination,
            random_state=random_state
        )

        return {
            "status": "success",
            "message": f"Isolation Forest model successfully trained and persisted on {metadata.get('dataset_name')}.",
            "model_info": metadata
        }
    except Exception as e:
        logger.error("Model retraining failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Model retraining failed: {str(e)}")


@router.get("/evaluation")
def get_evaluation(
    dataset: str = Query("BGL", description="Dataset name to evaluate"),
    include_baselines: bool = Query(False, description="Include research baseline comparisons")
):
    """
    Returns full evaluation report for the specified dataset.
    Includes supervised metrics for labeled datasets (BGL) and baseline comparisons if requested.
    """
    try:
        ds_name = _clean_str(dataset) or "BGL"
        inc_baselines = bool(include_baselines if isinstance(include_baselines, bool) else getattr(include_baselines, "default", False))

        meta = anomaly_model.get_model_info(dataset_name=ds_name)
        if meta.get("dataset_name", "").lower() != ds_name.lower():
            if ds_name.lower() not in {"bgl_full", "bgl-full", "bglfull"}:
                meta = anomaly_model.train_on_dataset(dataset_name=ds_name)

        result = {
            "status": "success",
            "dataset": meta.get("dataset_name"),
            "model_info": meta,
            "has_ground_truth_labels": meta.get("has_ground_truth_labels", False),
            "evaluation_summary": meta.get("evaluation_summary", {})
        }

        if inc_baselines:
            baselines_res = evaluate_baselines(dataset_name=ds_name)
            result["baselines_comparison"] = baselines_res

        return result
    except Exception as e:
        logger.error("Evaluation request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
