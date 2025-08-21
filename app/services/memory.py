from __future__ import annotations

from typing import Dict, List
from dataclasses import dataclass, field
import uuid
from app.models.schemas import AnalysisContext


@dataclass
class Session:
    id: str
    context: AnalysisContext
    messages: List[dict] = field(default_factory=list)


class MemoryStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    def create(self, context: AnalysisContext) -> Session:
        sid = uuid.uuid4().hex
        sess = Session(id=sid, context=context, messages=[])
        self._sessions[sid] = sess
        return sess

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        sess = self._sessions.get(session_id)
        if not sess:
            raise KeyError("session not found")
        sess.messages.append({"role": role, "content": content})

    def reset_history(self, session_id: str) -> None:
        sess = self._sessions.get(session_id)
        if sess:
            sess.messages.clear()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


memory_store = MemoryStore()

