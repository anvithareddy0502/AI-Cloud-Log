import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.app.services.log_parser import log_parser
from backend.app.services.anomaly_detector import anomaly_detector
from backend.app.services.event_correlator import event_correlator
from backend.app.database.connection import db

class AWSCloudWatchService:
    """
    AWS CloudWatch Logs Integration Service.
    Connects to AWS CloudWatch using boto3 to fetch log groups, streams,
    and recent log events for analysis by AI-CLAR.
    Gracefully handles missing or unconfigured AWS credentials.
    """

    def __init__(self):
        self.region = settings.AWS_REGION
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.default_log_group = settings.AWS_LOG_GROUP

    def is_configured(self) -> bool:
        """Returns True if AWS credentials and region are provided."""
        return bool(self.access_key and self.secret_key and self.region)

    def _get_client(self):
        if not self.is_configured():
            return None
        return boto3.client(
            "logs",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def get_log_groups(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves log groups from CloudWatch."""
        if not self.is_configured():
            return []
        try:
            client = self._get_client()
            if not client:
                return []
            response = client.describe_log_groups(limit=limit)
            return [
                {
                    "log_group_name": lg.get("logGroupName"),
                    "creation_time": lg.get("creationTime"),
                    "retention_days": lg.get("retentionInDays"),
                    "stored_bytes": lg.get("storedBytes", 0)
                }
                for lg in response.get("logGroups", [])
            ]
        except (ClientError, NoCredentialsError, BotoCoreError, Exception) as e:
            logger.warning("CloudWatch describe_log_groups failed: %s", e)
            return []

    def get_log_streams(self, log_group_name: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves log streams from a CloudWatch log group."""
        if not self.is_configured():
            return []
        group = log_group_name or self.default_log_group
        if not group:
            return []
        try:
            client = self._get_client()
            if not client:
                return []
            response = client.describe_log_streams(
                logGroupName=group,
                orderBy="LastEventTime",
                descending=True,
                limit=limit
            )
            return [
                {
                    "stream_name": stream.get("logStreamName"),
                    "creation_time": stream.get("creationTime"),
                    "first_event_timestamp": stream.get("firstEventTimestamp"),
                    "last_event_timestamp": stream.get("lastEventTimestamp"),
                    "stored_bytes": stream.get("storedBytes", 0)
                }
                for stream in response.get("logStreams", [])
            ]
        except (ClientError, NoCredentialsError, BotoCoreError, Exception) as e:
            logger.warning("CloudWatch describe_log_streams failed for group '%s': %s", group, e)
            return []

    def get_cloudwatch_logs(
        self,
        log_group_name: Optional[str] = None,
        log_stream_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches events from a specific log stream or group."""
        if not self.is_configured():
            return []
        group = log_group_name or self.default_log_group
        if not group:
            return []
        try:
            client = self._get_client()
            if not client:
                return []
            if log_stream_name:
                resp = client.get_log_events(
                    logGroupName=group,
                    logStreamName=log_stream_name,
                    limit=limit,
                    startFromHead=False
                )
                events = resp.get("events", [])
            else:
                resp = client.filter_log_events(
                    logGroupName=group,
                    limit=limit
                )
                events = resp.get("events", [])

            formatted = []
            for ev in events:
                ts_epoch = ev.get("timestamp", 0) / 1000.0
                dt = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
                formatted.append({
                    "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "message": ev.get("message", "").strip(),
                    "ingestion_time": ev.get("ingestionTime"),
                    "event_id": ev.get("eventId")
                })
            return formatted
        except (ClientError, NoCredentialsError, BotoCoreError, Exception) as e:
            logger.warning("CloudWatch get_cloudwatch_logs failed: %s", e)
            return []

    def get_recent_events(self, log_group_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves the most recent events across a log group."""
        return self.get_cloudwatch_logs(log_group_name=log_group_name, limit=limit)

    def ingest_from_cloudwatch(self, log_group_name: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Pulls recent CloudWatch log events, parses them, runs anomaly detection,
        and triggers multi-factor event correlation into AI-CLAR incidents.
        """
        if not self.is_configured():
            return {
                "success": False,
                "message": "AWS CloudWatch is not configured. Please supply AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in settings.",
                "logs_ingested": 0
            }

        events = self.get_recent_events(log_group_name=log_group_name, limit=limit)
        if not events:
            return {
                "success": True,
                "message": "Connected to AWS CloudWatch, but no recent events were found.",
                "logs_ingested": 0
            }

        raw_text = "\n".join(e["message"] for e in events)
        parsed_logs = log_parser.parse_content(raw_text, filename="aws-cloudwatch.log")
        if not parsed_logs:
            parsed_logs = []
            for ev in events:
                parsed_logs.append({
                    "id": ev.get("event_id") or f"cw-{datetime.now(timezone.utc).timestamp()}",
                    "timestamp": ev.get("timestamp"),
                    "server": "aws-ec2-node",
                    "service": "cloudwatch-service",
                    "severity": "INFO",
                    "message": ev.get("message"),
                    "raw": ev.get("message"),
                    "source": "aws_cloudwatch"
                })

        anomalies_detected = anomaly_detector.detect_anomalies(parsed_logs)
        
        db.logs.insert_many(parsed_logs)
        if anomalies_detected:
            db.anomalies.insert_many(anomalies_detected)

        incidents = event_correlator.correlate_and_create_incidents(parsed_logs)

        return {
            "success": True,
            "message": f"Successfully ingested {len(parsed_logs)} events from AWS CloudWatch.",
            "logs_ingested": len(parsed_logs),
            "anomalies_count": len(anomalies_detected),
            "incidents_created": len(incidents)
        }

aws_log_service = AWSCloudWatchService()

def is_configured() -> bool:
    return aws_log_service.is_configured()

def get_cloudwatch_logs(log_group_name: Optional[str] = None, log_stream_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    return aws_log_service.get_cloudwatch_logs(log_group_name, log_stream_name, limit)

def get_log_streams(log_group_name: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    return aws_log_service.get_log_streams(log_group_name, limit)

def get_recent_events(log_group_name: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    return aws_log_service.get_recent_events(log_group_name, limit)
