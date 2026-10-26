"""
CLI Training Command for AI-CLAR ML Anomaly Detection Pipeline
Supports:
    python -m backend.ml.train --dataset OpenStack
    python -m backend.ml.train --dataset HDFS
    python -m backend.ml.train --dataset BGL
    python -m backend.ml.train --dataset synthetic
"""
import sys
import argparse
import json
from backend.app.services.anomaly_model import anomaly_model
from backend.app.ml.dataset_adapters import dataset_adapter


def main():
    parser = argparse.ArgumentParser(
        description="AI-CLAR Machine Learning Model Training (Isolation Forest)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=[
            "OpenStack", "HDFS", "BGL", "BGL_2k", "BGL_full", "synthetic",
            "openstack", "hdfs", "bgl", "bgl_2k", "bgl_full"
        ],
        help="Dataset to train on (OpenStack, HDFS, BGL_2k, BGL_full, or synthetic)"
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.15,
        help="Expected proportion of outliers in the dataset (default: 0.15)"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Reproducible random seed (default: 42)"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional maximum records limit (useful for quick smoke-tests or sampling)"
    )

    args = parser.parse_args()
    ds_name = args.dataset

    print("=" * 70)
    print(f"AI-CLAR Machine Learning Training Pipeline")
    print(f"Target Dataset: {ds_name.upper()}")
    print(f"Algorithm:      Isolation Forest (Unsupervised)")
    print(f"Contamination:  {args.contamination}")
    print(f"Random Seed:    {args.random_state} (Reproducible 80/20 Train/Test Split)")
    if args.max_records:
        print(f"Record Limit:   {args.max_records} logs")
    print("=" * 70)

    try:
        metadata = anomaly_model.train_on_dataset(
            dataset_name=ds_name,
            contamination=args.contamination,
            random_state=args.random_state,
            max_records=args.max_records
        )

        eval_summary = metadata.get("evaluation_summary", {})
        print("\n[SUCCESS] Model training completed and persisted successfully.")
        print("-" * 70)
        print(f"Model Version:            {metadata.get('model_version')}")
        print(f"Dataset Name:             {metadata.get('dataset_name')}")
        print(f"Training Split:           {metadata.get('number_of_training_samples')} samples (80%)")
        print(f"Testing Split:            {metadata.get('number_of_testing_samples')} samples (20%)")
        print(f"Feature Dimension:        {metadata.get('number_of_features')} numerical features")
        print(f"Unsupervised Evaluation:  {eval_summary.get('predicted_anomalies_count')} outliers flagged ({eval_summary.get('anomaly_percentage')}%)")
        
        score_sum = eval_summary.get("anomaly_score_summary", {})
        print(f"Anomaly Score Summary:    min={score_sum.get('min')}, mean={score_sum.get('mean')}, max={score_sum.get('max')}, std={score_sum.get('std')}")

        if "supervised_metrics" in eval_summary:
            sm = eval_summary["supervised_metrics"]
            print("\n[BENCHMARK] Ground-Truth Supervised Validation (Unseen Test Split):")
            print(f"  Accuracy:               {sm.get('accuracy') * 100:.2f}%")
            print(f"  Precision:              {sm.get('precision') * 100:.2f}%")
            print(f"  Recall:                 {sm.get('recall') * 100:.2f}%")
            print(f"  F1-Score:               {sm.get('f1_score'):.4f}")
            print(f"  Matthews Corr (MCC):    {sm.get('mcc'):.4f}")
            print(f"  Confusion Matrix:       {sm.get('confusion_matrix')} (TN={sm.get('true_negatives')}, FP={sm.get('false_positives')}, FN={sm.get('false_negatives')}, TP={sm.get('true_positives')})")
            print(f"  False Positive Rate:    {sm.get('false_positive_rate') * 100:.2f}%")
            print(f"  False Negative Rate:    {sm.get('false_negative_rate') * 100:.2f}%")
        else:
            print(f"\n[NOTE] {eval_summary.get('evaluation_type')}")
            print("  Ground-truth labels are not present in this dataset. Supervised accuracy is omitted to prevent fabrication.")

        print("=" * 70)
        return 0

    except Exception as err:
        print(f"\n[ERROR] Training failed: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
