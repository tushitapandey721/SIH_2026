"""
Test Suite: SQLite Session Store & Regulatory Audit Logging
Verifies:
1. Direct SQLite database CRUD operations (Conversations, Messages, Audit Logs).
2. Cascade deletion of messages when a conversation is deleted.
3. FastAPI endpoints (/conversations, /conversations/{id}, /audit/logs).
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session_store import SessionStore
from fastapi.testclient import TestClient


class TestSessionStoreUnit(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for isolation
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = Path(self.temp_dir.name) / "test_sessions.db"
        self.store = SessionStore(db_path=self.db_path)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_create_and_get_conversation(self):
        created = self.store.create_conversation(title="Patent Query Session", jurisdiction="national")
        conv_id = created["id"]
        self.assertIsNotNone(conv_id)
        self.assertTrue(len(conv_id) > 10)

        conv = self.store.get_conversation(conv_id)
        self.assertIsNotNone(conv)
        self.assertEqual(conv["id"], conv_id)
        self.assertEqual(conv["title"], "Patent Query Session")
        self.assertEqual(conv["jurisdiction"], "national")

    def test_list_conversations(self):
        c1 = self.store.create_conversation(title="Session 1", jurisdiction="national")
        c2 = self.store.create_conversation(title="Session 2", jurisdiction="international")

        convs = self.store.list_conversations()
        conv_ids = [c["id"] for c in convs]
        self.assertIn(c1["id"], conv_ids)
        self.assertIn(c2["id"], conv_ids)
        self.assertGreaterEqual(len(convs), 2)

    def test_messages_crud_and_citations(self):
        created = self.store.create_conversation(title="Citation Test")
        conv_id = created["id"]
        
        # User query
        res1 = self.store.add_message(
            conversation_id=conv_id,
            message={
                "role": "user",
                "content": "What is Section 3(d)?",
                "language": "en"
            }
        )
        self.assertEqual(res1["status"], "persisted")

        # Assistant response with citations
        citations = [
            {"act_code": "PAT", "title": "Patents Act, 1970", "section": "Section 3(d)", "similarity": 0.92}
        ]
        res2 = self.store.add_message(
            conversation_id=conv_id,
            message={
                "role": "assistant",
                "content": "Section 3(d) prevents evergreening.",
                "language": "en",
                "citations": citations,
                "timing_ms": {"total": 310.5}
            }
        )
        self.assertEqual(res2["status"], "persisted")

        conv = self.store.get_conversation(conv_id)
        self.assertIsNotNone(conv)
        msgs = conv["messages"]
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[0]["content"], "What is Section 3(d)?")
        self.assertEqual(msgs[1]["role"], "assistant")
        self.assertEqual(msgs[1]["citations"][0]["section"], "Section 3(d)")
        self.assertAlmostEqual(msgs[1]["timing_ms"]["total"], 310.5, places=1)

    def test_audit_logs(self):
        created = self.store.create_conversation(title="Audit Test")
        conv_id = created["id"]
        self.store.log_audit_event(
            conversation_id=conv_id,
            query="test query for audit",
            detected_lang="en",
            jurisdiction="national",
            formulation_type="direct",
            provider_used="groq",
            abstained=False,
            latency_ms=150.0
        )

        logs = self.store.get_audit_logs(limit=10)
        self.assertGreaterEqual(len(logs), 1)
        found = any(l["query"] == "test query for audit" for l in logs)
        self.assertTrue(found)

    def test_delete_conversation_cascade(self):
        created = self.store.create_conversation(title="To Delete")
        conv_id = created["id"]
        self.store.add_message(conv_id, {"role": "user", "content": "Will be deleted"})
        
        self.assertTrue(self.store.delete_conversation(conv_id))
        self.assertIsNone(self.store.get_conversation(conv_id))


class TestApiEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.main import app
        cls.client = TestClient(app)

    def test_conversations_api(self):
        # 1. Create a conversation
        create_res = self.client.post("/conversations", json={"title": "FastAPI Test Session", "jurisdiction": "national"})
        self.assertEqual(create_res.status_code, 200)
        data = create_res.json()
        conv_id = data["id"]
        self.assertTrue(len(conv_id) > 10)

        # 2. List conversations
        list_res = self.client.get("/conversations")
        self.assertEqual(list_res.status_code, 200)
        convs = list_res.json().get("conversations", [])
        self.assertTrue(any(c["id"] == conv_id for c in convs))

        # 3. Get single conversation detail
        detail_res = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["id"], conv_id)
        self.assertEqual(detail["messages"], [])

        # 4. Check audit logs endpoint
        audit_res = self.client.get("/audit/logs")
        self.assertEqual(audit_res.status_code, 200)
        logs = audit_res.json().get("audit_logs", [])
        self.assertIsInstance(logs, list)

        # 5. Delete conversation
        del_res = self.client.delete(f"/conversations/{conv_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()["status"], "deleted")

        # 6. Verify 404 after deletion
        not_found_res = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(not_found_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
