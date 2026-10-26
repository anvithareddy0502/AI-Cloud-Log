import re
import copy
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.utils.logger import logger
from backend.data.mock_data import (
    SERVERS, INCIDENTS, ANOMALIES, SECURITY_EVENTS, MOCK_LOGS, REPORTS, ALERTS
)

class InMemoryCollection:
    """
    Lightweight, robust in-memory collection mimicking PyMongo API
    Used when local MongoDB instance is not available.
    """
    def __init__(self, name: str, initial_data: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self._data: List[Dict[str, Any]] = copy.deepcopy(initial_data or [])

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        for k, v in query.items():
            if k == "$or":
                return any(self._matches(doc, cond) for cond in v)
            if isinstance(v, dict):
                if "$regex" in v:
                    pattern = v["$regex"]
                    opts = v.get("$options", "")
                    flags = re.IGNORECASE if "i" in opts else 0
                    val = str(doc.get(k, ""))
                    if not re.search(pattern, val, flags):
                        return False
                elif "$in" in v:
                    if doc.get(k) not in v["$in"]:
                        return False
                elif "$gte" in v:
                    if str(doc.get(k, "")) < str(v["$gte"]):
                        return False
                elif "$lte" in v:
                    if str(doc.get(k, "")) > str(v["$lte"]):
                        return False
            else:
                if str(doc.get(k, "")).lower() != str(v).lower():
                    return False
        return True

    def insert_one(self, doc: Dict[str, Any]):
        doc_copy = copy.deepcopy(doc)
        if "_id" not in doc_copy and "id" in doc_copy:
            doc_copy["_id"] = doc_copy["id"]
        elif "_id" not in doc_copy:
            doc_copy["_id"] = f"{self.name}-{len(self._data)+1}"
        self._data.insert(0, doc_copy)
        return doc_copy

    def insert_many(self, docs: List[Dict[str, Any]]):
        for d in docs:
            self.insert_one(d)
        return docs

    def find(self, query: Optional[Dict[str, Any]] = None, sort_by: Optional[tuple] = None, limit: int = 0, skip: int = 0) -> List[Dict[str, Any]]:
        query = query or {}
        results = [copy.deepcopy(d) for d in self._data if self._matches(d, query)]
        if sort_by:
            field, direction = sort_by
            results.sort(key=lambda x: str(x.get(field, "")), reverse=(direction == -1))
        if skip > 0:
            results = results[skip:]
        if limit > 0:
            results = results[:limit]
        return results

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for d in self._data:
            if self._matches(d, query):
                return copy.deepcopy(d)
        return None

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        if not query:
            return len(self._data)
        return sum(1 for d in self._data if self._matches(d, query))

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        found = False
        for i, d in enumerate(self._data):
            if self._matches(d, query):
                found = True
                if "$set" in update:
                    self._data[i].update(update["$set"])
                break
        if not found and upsert:
            new_doc = copy.deepcopy(query)
            if "$set" in update:
                new_doc.update(update["$set"])
            self.insert_one(new_doc)

    def delete_many(self, query: Dict[str, Any]):
        self._data = [d for d in self._data if not self._matches(d, query)]

class Database:
    def __init__(self):
        self.is_connected = False
        self.client = None
        self.db = None
        
        # In-memory collections initialized with rich mock data
        self.in_memory_logs = InMemoryCollection("logs", MOCK_LOGS)
        self.in_memory_servers = InMemoryCollection("servers", SERVERS)
        self.in_memory_anomalies = InMemoryCollection("anomalies", ANOMALIES)
        self.in_memory_incidents = InMemoryCollection("incidents", INCIDENTS)
        self.in_memory_security = InMemoryCollection("security_events", SECURITY_EVENTS)
        self.in_memory_reports = InMemoryCollection("reports", REPORTS)
        self.in_memory_alerts = InMemoryCollection("alerts", ALERTS)

    def connect(self):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=1000)
            self.client.admin.command('ping')
            self.db = self.client[settings.DATABASE_NAME]
            self.is_connected = True
            logger.info("MongoDB connection established successfully at %s (%s)", settings.MONGODB_URI, settings.DATABASE_NAME)
            self._ensure_indexes()
            self._seed_if_empty()
        except Exception as e:
            self.is_connected = False
            logger.warning("MongoDB unavailable at %s (%s). Seamlessly operating with Resilient In-Memory Database.", settings.MONGODB_URI, e)

    def _ensure_indexes(self):
        if not self.is_connected or self.db is None:
            return
        try:
            self.db.logs.create_index([("timestamp", -1)])
            self.db.logs.create_index([("server", 1)])
            self.db.logs.create_index([("service", 1)])
            self.db.logs.create_index([("severity", 1)])
            self.db.anomalies.create_index([("timestamp", -1)])
            self.db.servers.create_index([("name", 1)], unique=True)
            self.db.alerts.create_index([("created_at", -1)])
            self.db.alerts.create_index([("alert_id", 1)], unique=True)
            logger.info("MongoDB collection indexes initialized.")
        except Exception as err:
            logger.warning("Failed to create MongoDB indexes: %s", err)

    def _seed_if_empty(self):
        if not self.is_connected or self.db is None:
            return
        try:
            if self.db.logs.count_documents({}) == 0:
                self.db.logs.insert_many(copy.deepcopy(MOCK_LOGS))
            if self.db.servers.count_documents({}) == 0:
                self.db.servers.insert_many(copy.deepcopy(SERVERS))
            if self.db.anomalies.count_documents({}) == 0:
                self.db.anomalies.insert_many(copy.deepcopy(ANOMALIES))
            if self.db.incidents.count_documents({}) == 0:
                self.db.incidents.insert_many(copy.deepcopy(INCIDENTS))
            if self.db.security_events.count_documents({}) == 0:
                self.db.security_events.insert_many(copy.deepcopy(SECURITY_EVENTS))
            if self.db.reports.count_documents({}) == 0:
                self.db.reports.insert_many(copy.deepcopy(REPORTS))
            if self.db.alerts.count_documents({}) == 0:
                self.db.alerts.insert_many(copy.deepcopy(ALERTS))
            logger.info("MongoDB collections pre-seeded with initial telemetry.")
        except Exception as err:
            logger.warning("Failed to seed initial data into MongoDB: %s", err)

    # Collection Accessors
    @property
    def logs(self):
        return self.db.logs if self.is_connected and self.db is not None else self.in_memory_logs

    @property
    def servers(self):
        return self.db.servers if self.is_connected and self.db is not None else self.in_memory_servers

    @property
    def anomalies(self):
        return self.db.anomalies if self.is_connected and self.db is not None else self.in_memory_anomalies

    @property
    def incidents(self):
        return self.db.incidents if self.is_connected and self.db is not None else self.in_memory_incidents

    @property
    def security_events(self):
        return self.db.security_events if self.is_connected and self.db is not None else self.in_memory_security

    @property
    def reports(self):
        return self.db.reports if self.is_connected and self.db is not None else self.in_memory_reports

    @property
    def alerts(self):
        return self.db.alerts if self.is_connected and self.db is not None else self.in_memory_alerts

db = Database()
