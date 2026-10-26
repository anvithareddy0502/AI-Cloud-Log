import uuid
from datetime import datetime
from typing import List, Dict, Any
from backend.app.database.connection import db
from backend.app.services.feature_extractor import feature_extractor
from backend.app.ml.anomaly_model import anomaly_model
from backend.app.utils.logger import logger

class AnomalyDetectorService:
    """
    Coordinates feature extraction, ML inference, and anomaly persistence in MongoDB.
    """

    def process_and_detect(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes ML pipeline on a batch of logs, detects anomalies, and stores them in MongoDB.
        """
        if not logs:
            return []

        # 1. Feature Extraction
        feature_windows = feature_extractor.extract_features(logs)
        logger.info("Extracted %d feature window(s) across monitored servers.", len(feature_windows))

        new_anomalies = []

        # 2. ML Evaluation per window
        for f in feature_windows:
            eval_res = anomaly_model.evaluate_window(f)
            if eval_res["is_anomaly"]:
                server = f["server"]
                services = f.get("services", ["cloud-service"])
                primary_service = services[0] if services else "cloud-service"

                # Craft clean human-readable title
                if "critical" in eval_res["reason"].lower():
                    title = f"Critical Service Degradation on {server.upper()}"
                elif "auth" in eval_res["reason"].lower() or "login" in eval_res["reason"].lower():
                    title = f"Abnormal Failed Auth Spike on {server.upper()}"
                elif "5xx" in eval_res["reason"].lower() or "database" in eval_res["reason"].lower():
                    title = f"Database & Gateway Error Surge on {server.upper()}"
                elif "latency" in eval_res["reason"].lower():
                    title = f"Response Latency Degradation on {server.upper()}"
                else:
                    title = f"Telemetry Anomaly Detected on {server.upper()}"

                anomaly_doc = {
                    "id": f"anom-{uuid.uuid4().hex[:8]}",
                    "server": server,
                    "service": primary_service,
                    "title": title,
                    "time_window": f["time_window"],
                    "detection_time": "just now",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "anomaly_score": eval_res["anomaly_score"],
                    "confidence": eval_res["confidence"],
                    "severity": eval_res["severity"],
                    "reason": eval_res["reason"],
                    "status": "Active",
                    "baseline_value": "Normal cluster throughput",
                    "observed_value": f"{f['error_count']} errors ({int(f['error_rate']*100)}% rate)",
                    "features": f
                }

                # 3. Store in MongoDB anomalies collection
                try:
                    db.anomalies.insert_one(anomaly_doc)
                    new_anomalies.append(anomaly_doc)
                    logger.info("Detected & saved anomaly: %s (%s) [Score: %.2f]", title, server, eval_res["anomaly_score"])
                except Exception as err:
                    logger.error("Failed to persist anomaly to database: %s", err)

        return new_anomalies

    def detect_anomalies(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.process_and_detect(logs)

anomaly_detector_service = AnomalyDetectorService()
anomaly_detector = anomaly_detector_service
