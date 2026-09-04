"""SQLite-backed conversation session store and regulatory audit logging for IP-SAKTI Sahayak."""

import os
import csv
import json
import uuid
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("IP-SAKTI.SessionStore")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ip_sakti.db"
DEFAULT_AUDIT_LOG_CSV = PROJECT_ROOT / "data" / "audit_log.csv"
DEFAULT_AUDIT_LOG_FILE = PROJECT_ROOT / "data" / "audit_log"


class SessionStore:
    """Manages conversational session persistence, message histories, and regulatory audit logs."""

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection configured with WAL journal mode and row dict factory."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        """Creates tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    jurisdiction TEXT NOT NULL DEFAULT 'national',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations TEXT DEFAULT '[]',
                    classification TEXT,
                    classification_citation TEXT,
                    confidence TEXT,
                    abstained INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'en',
                    provider_used TEXT,
                    timing_ms TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    is_error INTEGER DEFAULT 0,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT,
                    query TEXT NOT NULL,
                    detected_lang TEXT NOT NULL DEFAULT 'en',
                    jurisdiction TEXT NOT NULL DEFAULT 'national',
                    formulation_type TEXT,
                    provider_used TEXT,
                    abstained INTEGER DEFAULT 0,
                    latency_ms REAL NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);

                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    query TEXT,
                    answer_snippet TEXT,
                    citations TEXT,
                    rating TEXT NOT NULL,
                    comment TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);
            """)
            conn.commit()
        logger.info(f"Initialized SQLite session store at {self.db_path}")
        self._init_audit_file()

    def _init_audit_file(self) -> None:
        """Ensures append-only audit files (/data/audit_log.csv and /data/audit_log) exist and backfills existing SQLite logs if empty."""
        try:
            for log_path in [DEFAULT_AUDIT_LOG_CSV, DEFAULT_AUDIT_LOG_FILE]:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                if not log_path.exists() or log_path.stat().st_size == 0:
                    with open(log_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            "timestamp",
                            "jurisdiction",
                            "query",
                            "classification",
                            "provider_used",
                            "latency_ms",
                            "abstained",
                            "conversation_id",
                            "detected_lang",
                        ])
                        with self._get_connection() as conn:
                            rows = conn.execute(
                                "SELECT * FROM audit_logs ORDER BY id ASC"
                            ).fetchall()
                            for r in rows:
                                writer.writerow([
                                    r["timestamp"],
                                    r["jurisdiction"],
                                    r["query"].replace("\n", " ").strip(),
                                    r["formulation_type"] or "",
                                    r["provider_used"] or "none",
                                    round(float(r["latency_ms"]), 2),
                                    1 if r["abstained"] else 0,
                                    r["conversation_id"] or "",
                                    r["detected_lang"] or "en",
                                ])
        except Exception as e:
            logger.warning(f"Audit log file initialization note: {e}")

    def create_conversation(
        self,
        title: str,
        jurisdiction: str = "national",
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new conversation thread."""
        c_id = conversation_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, title, jurisdiction, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (c_id, title[:100], jurisdiction.lower(), now, now),
            )
            conn.commit()
        return {
            "id": c_id,
            "title": title[:100],
            "jurisdiction": jurisdiction.lower(),
            "created_at": now,
            "updated_at": now,
        }

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves conversation metadata and all associated messages."""
        with self._get_connection() as conn:
            conv_row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if not conv_row:
                return None

            messages_rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,),
            ).fetchall()

            messages = []
            for row in messages_rows:
                citations = json.loads(row["citations"]) if row["citations"] else []
                timing_ms = json.loads(row["timing_ms"]) if row["timing_ms"] else {}
                messages.append({
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "citations": citations,
                    "classification": row["classification"],
                    "classification_citation": row["classification_citation"],
                    "confidence": row["confidence"],
                    "abstained": bool(row["abstained"]),
                    "language": row["language"],
                    "provider_used": row["provider_used"],
                    "timing_ms": timing_ms,
                    "timestamp": row["timestamp"],
                    "isError": bool(row["is_error"]),
                })

            return {
                "id": conv_row["id"],
                "title": conv_row["title"],
                "jurisdiction": conv_row["jurisdiction"],
                "created_at": conv_row["created_at"],
                "updated_at": conv_row["updated_at"],
                "messages": messages,
            }

    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lists recent conversations with their message counts and preview snippet."""
        with self._get_connection() as conn:
            query = """
                SELECT c.*,
                       COUNT(m.id) AS message_count,
                       MAX(m.timestamp) AS last_message_time
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """
            rows = conn.execute(query, (limit,)).fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "jurisdiction": row["jurisdiction"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "message_count": row["message_count"],
                    "last_message_time": row["last_message_time"],
                }
                for row in rows
            ]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes a conversation and its cascaded messages."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_message(self, conversation_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Appends a message to a conversation, updating the conversation timestamp."""
        # Ensure parent conversation exists
        self.create_conversation(
            title=message.get("content", "New Inquiry")[:50],
            jurisdiction=message.get("jurisdiction", "national"),
            conversation_id=conversation_id,
        )

        msg_id = message.get("id") or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        timestamp = message.get("timestamp") or now

        citations_json = json.dumps(message.get("citations") or [])
        timing_json = json.dumps(message.get("timing_ms") or {})

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (
                    id, conversation_id, role, content, citations,
                    classification, classification_citation, confidence,
                    abstained, language, provider_used, timing_ms,
                    timestamp, is_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    msg_id,
                    conversation_id,
                    message.get("role", "user"),
                    message.get("content", ""),
                    citations_json,
                    message.get("classification"),
                    message.get("classification_citation"),
                    message.get("confidence"),
                    1 if message.get("abstained") else 0,
                    message.get("language", "en"),
                    message.get("provider_used"),
                    timing_json,
                    timestamp,
                    1 if message.get("isError") else 0,
                ),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            conn.commit()

        return {"id": msg_id, "conversation_id": conversation_id, "status": "persisted"}

    def log_audit_event(
        self,
        conversation_id: Optional[str],
        query: str,
        detected_lang: str,
        jurisdiction: str,
        formulation_type: Optional[str] = None,
        provider_used: Optional[str] = None,
        abstained: bool = False,
        latency_ms: float = 0.0,
        classification: Optional[str] = None,
    ) -> None:
        """Logs a regulatory inquiry audit event to SQLite and append-only CSV log (DPDP data-minimized, no PII)."""
        now = datetime.now(timezone.utc).isoformat()
        resolved_class = classification or formulation_type
        # 1. Insert into SQLite table audit_logs
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (
                        conversation_id, query, detected_lang, jurisdiction,
                        formulation_type, provider_used, abstained, latency_ms, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        query,
                        detected_lang,
                        jurisdiction.lower(),
                        resolved_class,
                        provider_used,
                        1 if abstained else 0,
                        float(latency_ms),
                        now,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record audit log in SQLite: {e}")

        # 2. Append to append-only files (/data/audit_log.csv and /data/audit_log)
        try:
            for log_path in [DEFAULT_AUDIT_LOG_CSV, DEFAULT_AUDIT_LOG_FILE]:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_exists = log_path.exists() and log_path.stat().st_size > 0
                with open(log_path, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            "timestamp",
                            "jurisdiction",
                            "query",
                            "classification",
                            "provider_used",
                            "latency_ms",
                            "abstained",
                            "conversation_id",
                            "detected_lang",
                        ])
                    writer.writerow([
                        now,
                        jurisdiction.lower(),
                        query.replace("\n", " ").strip(),
                        resolved_class or "",
                        provider_used or "none",
                        round(float(latency_ms), 2),
                        1 if abstained else 0,
                        conversation_id or "",
                        detected_lang or "en",
                    ])
        except Exception as e:
            logger.error(f"Failed to append to audit log file: {e}")

    def get_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent regulatory audit logs with DPDP-minimized metadata."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "jurisdiction": row["jurisdiction"],
                    "query": row["query"],
                    "classification": row["formulation_type"],
                    "formulation_type": row["formulation_type"],
                    "provider_used": row["provider_used"],
                    "latency_ms": round(float(row["latency_ms"]), 2),
                    "abstained": bool(row["abstained"]),
                    "conversation_id": row["conversation_id"],
                    "detected_lang": row["detected_lang"],
                }
                for row in rows
            ]

    def log_feedback(
        self,
        rating: str,
        conversation_id: Optional[str] = None,
        query: Optional[str] = None,
        answer_snippet: Optional[str] = None,
        citations: Optional[List[Any]] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Records user feedback (up/down) with query, answer snippet, citations, and optional comment."""
        fb_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        citations_json = json.dumps(citations or [])
        clean_snippet = (answer_snippet or "")[:500]
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO feedback (id, conversation_id, query, answer_snippet, citations, rating, comment, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fb_id,
                        conversation_id,
                        query or "",
                        clean_snippet,
                        citations_json,
                        rating.lower().strip(),
                        comment.strip() if comment else None,
                        now,
                    ),
                )
                conn.commit()
            logger.info(f"Recorded feedback {fb_id} ({rating}) for conversation '{conversation_id}'")
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")

        return {
            "id": fb_id,
            "conversation_id": conversation_id,
            "query": query,
            "answer_snippet": clean_snippet,
            "citations": citations or [],
            "rating": rating.lower().strip(),
            "comment": comment,
            "timestamp": now,
        }

    def get_feedback_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent user feedback entries."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "conversation_id": row["conversation_id"],
                    "query": row["query"],
                    "answer_snippet": row["answer_snippet"],
                    "citations": json.loads(row["citations"]) if row["citations"] else [],
                    "rating": row["rating"],
                    "comment": row["comment"],
                    "timestamp": row["timestamp"],
                }
                for row in rows
            ]


# Singleton instance
_default_session_store: Optional[SessionStore] = None


def get_default_session_store() -> SessionStore:
    global _default_session_store
    if _default_session_store is None:
        _default_session_store = SessionStore()
    return _default_session_store
