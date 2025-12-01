# memory_service.py
# Memory module for enterprise agents: Session Memory + Long-Term Memory + Context Compaction

import json
import os
import time
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from difflib import get_close_matches

SESSIONS_DIR = "sessions"
MEMORY_FILE = "memory_bank.json"
_LOCK = threading.Lock()


def _now_iso() -> str:
    """Returns current time in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


# ============================================================
# SESSION (SHORT-TERM) MEMORY
# ============================================================

class SessionMemory:
    """In-memory session storage + optional disk checkpoints."""
    _sessions: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_session(cls, session_id: str, metadata: Optional[Dict] = None) -> Dict:
        with _LOCK:
            if session_id in cls._sessions:
                return cls._sessions[session_id]

            cls._sessions[session_id] = {
                "id": session_id,
                "created_at": _now_iso(),
                "metadata": metadata or {},
                "history": []
            }
            return cls._sessions[session_id]

    @classmethod
    def save(cls, session_id: str, record: Dict[str, Any], checkpoint: bool = False) -> Dict:
        with _LOCK:
            session = cls.create_session(session_id)
            event = {"ts": _now_iso(), "record": record}
            session["history"].append(event)

            if checkpoint:
                cls.checkpoint(session_id)

            return event

    @classmethod
    def get_history(cls, session_id: str, last_n: Optional[int] = None) -> List[Dict]:
        session = cls._sessions.get(session_id)
        if not session:
            return []

        if last_n:
            return session["history"][-last_n:]
        return session["history"]

    @classmethod
    def checkpoint(cls, session_id: str) -> bool:
        """Persist session history to disk."""
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        session = cls._sessions.get(session_id)

        if not session:
            return False

        path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

        return True

    @classmethod
    def load_checkpoint(cls, session_id: str) -> Optional[Dict]:
        path = os.path.join(SESSIONS_DIR, f"{session_id}.json")

        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with _LOCK:
            cls._sessions[session_id] = data

        return data

    @classmethod
    def clear(cls, session_id: str) -> bool:
        with _LOCK:
            if session_id in cls._sessions:
                del cls._sessions[session_id]

        path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)

        return True


# ============================================================
# LONG-TERM MEMORY BANK
# ============================================================

class MemoryBank:
    """Simple persistent memory store with fuzzy + tag search."""

    def __init__(self, filepath: str = MEMORY_FILE):
        self.filepath = filepath
        self._data: List[Dict[str,Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                backup = f"{self.filepath}.backup.{int(time.time())}"
                os.rename(self.filepath, backup)
                self._data = []
        else:
            self._data = []

    def _persist(self):
        tmp_path = f"{self.filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.filepath)

    def add(self, text: str, tags: Optional[List[str]] = None, meta: Optional[Dict] = None) -> Dict:
        record = {
            "id": f"mem_{int(time.time() * 1000)}",
            "created_at": _now_iso(),
            "tags": tags or [],
            "text": text,
            "meta": meta or {}
        }
        self._data.append(record)
        self._persist()
        return record

    def query(self, query_text: str, top_k: int = 5, by_tags: bool = False) -> List[Dict]:
        results: List[Tuple[float, Dict]] = []

        # Tag search mode
        if by_tags:
            query_tags = set(tag.strip().lower() for tag in query_text.split())
            for rec in self._data:
                rec_tags = set(tag.lower() for tag in rec.get("tags", []))
                match_score = len(query_tags & rec_tags)
                if match_score > 0:
                    results.append((match_score, rec))
            results.sort(key=lambda x: x[0], reverse=True)
            return [r for _, r in results[:top_k]]

        # Exact substring matching
        exact = []
        for rec in self._data:
            if query_text.lower() in rec.get("text", "").lower():
                exact.append((1.0, rec))

        if exact:
            return [r for _, r in exact[:top_k]]

        # Fuzzy match
        texts = [rec["text"] for rec in self._data]
        fuzzy_hits = get_close_matches(query_text, texts, n=top_k, cutoff=0.4)

        output = []
        for hit in fuzzy_hits:
            for rec in self._data:
                if rec["text"] == hit and rec not in output:
                    output.append(rec)

        return output

    def delete(self, mem_id: str) -> bool:
        before = len(self._data)
        self._data = [rec for rec in self._data if rec["id"] != mem_id]

        if len(self._data) < before:
            self._persist()
            return True
        return False

    def export(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        return path

    def all(self) -> List[Dict]:
        return list(self._data)


# ============================================================
# CONTEXT COMPACTION
# ============================================================

def compact_context_by_age(history: List[Dict], max_items: int = 10) -> List[Dict]:
    return history[-max_items:] if history else []


def compact_context_by_importance(history: List[Dict], max_items: int = 10) -> List[Dict]:
    if not history:
        return []

    scored = []
    for event in history:
        record = event.get("record", {})
        score = 0

        if record.get("meta", {}).get("importance") == "high":
            score += 3

        if record.get("type") in ("tool_call", "final_response"):
            score += 2

        try:
            event_time = datetime.fromisoformat(event["ts"].replace("Z", "")).timestamp()
            if time.time() - event_time < 3600:
                score += 1
        except Exception:
            pass

        scored.append((score, event))

    scored.sort(key=lambda x: x[0], reverse=True)
    compact = [ev for _, ev in scored[:max_items]]
    compact.sort(key=lambda x: x["ts"])
    return compact


def compact_context_with_summarizer(history: List[Dict], max_chars: int = 2000, summarizer_fn=None) -> List[Dict]:
    if not history:
        return []

    if summarizer_fn is None:
        return compact_context_by_age(history)

    recent = history[-5:]
    older = history[:-5]

    if not older:
        return recent

    combined = "\n".join(json.dumps(ev, ensure_ascii=False) for ev in older)
    combined = combined[:max_chars]

    try:
        summary = summarizer_fn(combined)
        synthetic_event = {
            "ts": _now_iso(),
            "record": {"type": "summary", "text": summary}
        }
        return recent + [synthetic_event]
    except Exception:
        return compact_context_by_age(history)


# ============================================================
# MEMORY SERVICE FACADE (NEEDED BY MULTI AGENT SYSTEM)
# ============================================================

class MemoryService:
    """Unified interface combining SessionMemory + MemoryBank."""

    def __init__(self):
        self.memory_bank = MemoryBank()

    # ---- SESSION MEMORY ----
    def start_session(self, session_id: str = None, metadata=None):
        if not session_id:
            session_id = f"session_{int(time.time() * 1000)}"
        return SessionMemory.create_session(session_id, metadata)

    def add_message(self, session_id: str, role: str, message: str):
        record = {"type": "message", "role": role, "text": message}
        return SessionMemory.save(session_id, record)

    def get_session_history(self, session_id: str, last_n=None):
        return SessionMemory.get_history(session_id, last_n)

    # ---- LONG-TERM MEMORY ----
    def remember(self, text: str, tags=None, meta=None):
        return self.memory_bank.add(text, tags, meta)

    def recall(self, query: str, top_k=5, by_tags=False):
        return self.memory_bank.query(query, top_k, by_tags)

    def forget(self, mem_id: str):
        return self.memory_bank.delete(mem_id)

    def export(self, path="memory_export.json"):
        return self.memory_bank.export(path)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    sid = "demo"
    SessionMemory.create_session(sid)
    SessionMemory.save(sid, {"type": "msg", "text": "hello"})
    SessionMemory.save(sid, {"type": "tool_call", "text": "search refund"}, checkpoint=True)

    print("Session history:", SessionMemory.get_history(sid))

    kb = MemoryBank()
    kb.add("Refund policy: takes 7 days", tags=["refund", "policy"])
    kb.add("Troubleshooting guide for network issues", tags=["tech"])

    print("Query refund:", kb.query("refund"))
