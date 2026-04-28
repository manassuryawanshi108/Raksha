"""Firebase Firestore database — real client when credentials are present,
   in-memory mock when they are not (local dev / demo mode)."""

import os
import uuid
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account


# ── In-memory store ─────────────────────────────────────────────────────────

class _MemCollection:
    """Minimal Firestore-like collection backed by a plain dict."""

    def __init__(self):
        self._docs: Dict[str, Dict] = {}

    # --- writes ---
    def add(self, data: dict):
        doc_id = str(uuid.uuid4())
        self._docs[doc_id] = dict(data)
        # Return a tuple like Firestore does: (timestamp, DocumentReference-like)
        ref = type("Ref", (), {"id": doc_id})()
        return (None, ref)

    def document(self, doc_id: str):
        return _MemDocument(self._docs, doc_id)

    # --- reads ---
    def stream(self):
        return [_MemSnapshot(doc_id, data) for doc_id, data in self._docs.items()]

    def where(self, field, op, value):
        return _MemQuery(self._docs, field, op, value)

    def limit(self, n):
        return _MemQuery(self._docs, limit=n)


class _MemDocument:
    def __init__(self, store: dict, doc_id: str):
        self._store = store
        self._id = doc_id

    def get(self):
        data = self._store.get(self._id)
        return _MemSnapshot(self._id, data) if data is not None else _MemSnapshotMissing()

    def set(self, data: dict):
        self._store[self._id] = dict(data)

    def update(self, data: dict):
        if self._id in self._store:
            self._store[self._id].update(data)
        else:
            self._store[self._id] = dict(data)

    def delete(self):
        self._store.pop(self._id, None)


class _MemSnapshot:
    def __init__(self, doc_id: str, data: dict):
        self.id = doc_id
        self._data = dict(data) if data else {}
        self.exists = True

    def to_dict(self):
        return dict(self._data)


class _MemSnapshotMissing:
    id = None
    exists = False
    def to_dict(self): return {}


class _MemQuery:
    def __init__(self, store: dict, field=None, op=None, value=None, limit=None):
        self._store = store
        self._field = field
        self._op = op
        self._value = value
        self._limit = limit

    def stream(self):
        results = []
        for doc_id, data in self._store.items():
            if self._field:
                dv = data.get(self._field)
                if self._op == "==" and dv != self._value:
                    continue
            results.append(_MemSnapshot(doc_id, data))
        if self._limit:
            results = results[:self._limit]
        return results

    def where(self, field, op, value):
        # chain — simplistic: apply additional filter on top
        filtered = {k: v for k, v in self._store.items()
                    if self._field is None or v.get(self._field) == self._value}
        q = _MemQuery(filtered, field, op, value, self._limit)
        return q

    def limit(self, n):
        self._limit = n
        return self


class _MemDB:
    """Thin wrapper that looks like firestore.Client.collection()."""

    def __init__(self):
        self._collections: Dict[str, _MemCollection] = {}

    def collection(self, name: str) -> _MemCollection:
        if name not in self._collections:
            self._collections[name] = _MemCollection()
        return self._collections[name]

    def batch(self):
        return _MemBatch(self)


class _MemBatch:
    def __init__(self, db):
        self._db = db
        self._ops = []

    def create(self, ref, data):
        self._ops.append((ref, data))

    def commit(self):
        for ref, data in self._ops:
            ref._store[ref._id] = dict(data)


# ── FirebaseDB ───────────────────────────────────────────────────────────────

class FirebaseDB:
    """Firebase Firestore database handler with in-memory fallback."""

    def __init__(self):
        self.db = None
        self._mode = "unknown"
        self.initialize()

    def initialize(self) -> None:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.getenv("FIREBASE_PROJECT_ID", "solution-82b83")

        if credentials_path and os.path.exists(credentials_path):
            try:
                from google.cloud import firestore
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.db = firestore.Client(credentials=credentials, project=project_id)
                self._mode = "firestore"
                print("[DB] Connected to Firebase Firestore")
                return
            except Exception as e:
                print(f"[DB] Firebase init failed: {e}")

        # In-memory fallback
        self.db = _MemDB()
        self._mode = "memory"
        print("[DB] Running in-memory database (no Firebase credentials found)")

    # ==================== NGO Issues ====================

    def add_issue(self, issue_data: Dict[str, Any]) -> str:
        doc_ref = self.db.collection("issues").add(issue_data)
        return doc_ref[1].id

    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection("issues").document(issue_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def get_all_issues(self) -> List[Dict[str, Any]]:
        return [{**doc.to_dict(), "id": doc.id} for doc in self.db.collection("issues").stream()]

    def get_pending_issues(self) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("issues").where("status", "==", "pending").stream()
        ]

    def update_issue(self, issue_id: str, update_data: Dict[str, Any]) -> bool:
        self.db.collection("issues").document(issue_id).update(update_data)
        return True

    def delete_issue(self, issue_id: str) -> bool:
        self.db.collection("issues").document(issue_id).delete()
        return True

    def batch_add_issues(self, issues: List[Dict[str, Any]]) -> List[str]:
        batch = self.db.batch()
        ids = []
        for issue in issues:
            col = self.db.collection("issues")
            doc_id = str(uuid.uuid4())
            doc_ref = col.document(doc_id)
            batch.create(doc_ref, issue)
            ids.append(doc_id)
        batch.commit()
        return ids

    # ==================== Volunteers ====================

    def add_volunteer(self, volunteer_data: Dict[str, Any]) -> str:
        doc_ref = self.db.collection("volunteers").add(volunteer_data)
        return doc_ref[1].id

    def get_volunteer(self, volunteer_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection("volunteers").document(volunteer_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def get_all_volunteers(self) -> List[Dict[str, Any]]:
        return [{**doc.to_dict(), "id": doc.id} for doc in self.db.collection("volunteers").stream()]

    def get_available_volunteers(self) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("volunteers").where("status", "==", "available").stream()
        ]

    def update_volunteer(self, volunteer_id: str, update_data: Dict[str, Any]) -> bool:
        self.db.collection("volunteers").document(volunteer_id).update(update_data)
        return True

    # ==================== Tasks ====================

    def create_task(self, task_data: Dict[str, Any]) -> str:
        doc_ref = self.db.collection("tasks").add(task_data)
        return doc_ref[1].id

    def get_tasks_by_volunteer(self, volunteer_id: str) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("tasks").where("volunteer_id", "==", volunteer_id).stream()
        ]

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("tasks").where("status", "==", "assigned").stream()
        ]

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return [{**doc.to_dict(), "id": doc.id} for doc in self.db.collection("tasks").stream()]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection("tasks").document(task_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        self.db.collection("tasks").document(task_id).update(update_data)
        return True

    # ==================== Users ====================

    def create_user(self, user_data: Dict[str, Any]) -> str:
        doc_ref = self.db.collection("users").add(user_data)
        return doc_ref[1].id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection("users").document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        docs = self.db.collection("users").where("email", "==", email).stream()
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        return [{**doc.to_dict(), "id": doc.id} for doc in self.db.collection("users").stream()]

    def get_users_by_status(self, status: str) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("users").where("status", "==", status).stream()
        ]

    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        return [
            {**doc.to_dict(), "id": doc.id}
            for doc in self.db.collection("users").where("role", "==", role).stream()
        ]

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        self.db.collection("users").document(user_id).update(update_data)
        return True

    # ==================== Tokens ====================

    def store_token(self, token: str, user_id: str) -> None:
        key = token.split(":")[0] if ":" in token else token
        self.db.collection("tokens").document(key).set({"token": token, "user_id": user_id})

    def verify_token(self, token: str) -> Optional[str]:
        docs = self.db.collection("tokens").where("token", "==", token).stream()
        for doc in docs:
            return doc.to_dict().get("user_id")
        return None


# Singleton
db = FirebaseDB()
