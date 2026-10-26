"""
CLI Evaluation Command for AI-CLAR ML Anomaly Detection Pipeline
Supports:
    python -m backend.ml.evaluate --dataset OpenStack
    python -m backend.ml.evaluate --dataset HDFS
    python -m backend.ml.evaluate --dataset BGL
    python -m backend.ml.evaluate --dataset BGL --include-baselines
"""
import sys
import argparse
from backend.app.services.anomaly_model import anomaly_model
from backend.app.ml.baselines import evaluate_baselines


def main():
    parser = argparse.ArgumentParser(
        description="AI-CLAR Machine Learning Model Evaluation (Isolation Forest & Baselines)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=[
            "OpenStack", "HDFS", "BGL", "BGL_2k", "BGL_full", "synthetic",
            "openstack", "hdfs", "bgl", "bgl_2k", "bgl_full"
        ],
        help="Dataset to evaluate (OpenStack, HDFS, BGL_2k, BGL_full, or synthetic)"
    )
    parser.add_argument(
        "--include-baselines",
        action="store_true",
        help="Also run research baseline models (Random Forest, Logistic Regression, SVM, LOF, One-Class SVM)"
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
        help="Optional maximum records limit for quick evaluation or testing"
    )

    args = parser.parse_args()
    ds_name = args.dataset

    print("=" * 75)
    print(f"AI-CLAR Machine Learning Evaluation Report")
    print(f"Target Dataset:      {ds_name.upper()}")
    print(f"Evaluation Protocol: 20% Unseen Test Split (Random Seed: {args.random_state})")
    if args.max_records:
        print(f"Record Limit:        {args.max_records} logs")
    print("=" * 75)

    try:
        # 1. Primary Model Evaluation (Isolation Forest)
        meta = anomaly_model.get_model_info(dataset_name=ds_name)
        # If current loaded model is not this dataset or not trained yet, train/load it
        if meta.get("dataset_name", "").lower() != ds_name.lower() or meta.get("training_status") != "Trained":
            if ds_name.lower() in {"bgl_full", "bgl-full", "bglfull"} and not args.max_records:
                print("\n[NOTICE] Model for BGL_full has not been trained yet.")
                print("To train on the full 4.6M log dataset, run:")
                print("  python -m backend.ml.train --dataset BGL_full")
                print("Or to run a quick evaluation sample, provide: --max-records 1000")
                return 0
            meta = anomaly_model.train_on_dataset(ds_name, random_state=args.random_state, max_records=args.max_records)

        eval_summary = meta.get("evaluation_summary", {})
        print("\n[PRIMARY MODEL] Isolation Forest (Unsupervised Tree Ensemble)")
        print("-" * 75)
        print(f"Status:                 {meta.get('training_status', 'Trained')}")
        print(f"Training Samples:       {meta.get('number_of_training_samples')}")
        print(f"Test Samples:           {meta.get('number_of_testing_samples')}")
        print(f"Feature Count:          {meta.get('number_of_features')}")
        print(f"Predicted Outliers:     {eval_summary.get('predicted_anomalies_count')} ({eval_summary.get('anomaly_percentage')}%)")

        score_sum = eval_summary.get("anomaly_score_summary", {})
        print(f"Score Distribution:     min={score_sum.get('min')}, mean={score_sum.get('mean')}, max={score_sum.get('max')}, std={score_sum.get('std')}")

        if "supervised_metrics" in eval_summary:
            sm = eval_summary["supervised_metrics"]
            print(f"\nGround-Truth Benchmark Metrics (Unseen Test Data):")
            print(f"  Accuracy:             {sm.get('accuracy') * 100:.2f}%")
            print(f"  Precision:            {sm.get('precision') * 100:.2f}%")
            print(f"  Recall:               {sm.get('recall') * 100:.2f}%")
            print(f"  F1-Score:             {sm.get('f1_score'):.4f}")
            print(f"  Matthews Corr (MCC):  {sm.get('mcc'):.4f}")
            print(f"  Confusion Matrix:     {sm.get('confusion_matrix')} (TN={sm.get('true_negatives')}, FP={sm.get('false_positives')}, FN={sm.get('false_negatives')}, TP={sm.get('true_positives')})")
            print(f"  False Positive Rate:  {sm.get('false_positive_rate') * 100:.2f}%")
            print(f"  False Negative Rate:  {sm.get('false_negative_rate') * 100:.2f}%")
        else:
            print(f"\nNote: {eval_summary.get('evaluation_type')}")
            print("  This dataset has no ground-truth failure labels; reporting empirical outlier distributions.")

        # 2. Optional Baseline Models Comparison
        if args.include_baselines:
            print("\n" + "=" * 75)
            print("[RESEARCH BASELINES] Comparative Model Evaluation on Unseen Test Split:")
            print("=" * 75)
            b_results = evaluate_baselines(dataset_name=ds_name, random_state=args.random_state, max_records=args.max_records)
            
            print(f"{'Model':<30} | {'Paradigm':<24} | {'Outliers':<10} | {'Accuracy':<8} | {'Precision':<10} | {'Recall':<8} | {'F1-Score':<8} | {'MCC':<8}")
            print("-" * 125)
            for m_name, m_info in b_results.get("models", {}).items():
                out_str = f"{m_info.get('outliers_flagged')} ({m_info.get('outlier_percentage')}%)"
                acc_str = f"{m_info.get('accuracy', '-')}"
                prec_str = f"{m_info.get('precision', '-')}"
                rec_str = f"{m_info.get('recall', '-')}"
                f1_str = f"{m_info.get('f1_score', '-')}"
                mcc_str = f"{m_info.get('mcc', '-')}"
                print(f"{m_name:<30} | {m_info.get('paradigm', ''):<24} | {out_str:<10} | {acc_str:<8} | {prec_str:<10} | {rec_str:<8} | {f1_str:<8} | {mcc_str:<8}")

        print("\n" + "=" * 75)
        return 0

    except Exception as err:
        print(f"\n[ERROR] Evaluation failed: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
