from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class AnalysisContext(BaseModel):
    diagnosis: str = Field(..., description="질환명")
    summary: Optional[str] = Field(None, description="소견/요약")
    similar_diseases: List[str] = Field(default_factory=list, description="유사질환 목록")
    refined_symptoms: Optional[str] = Field(None, description="정제된 증상 문장")


class InitSessionRequest(BaseModel):
    diagnosis: str
    summary: Optional[str] = None
    similar_diseases: Optional[List[str]] = None
    refined_symptoms: Optional[str] = None


class InitSessionResponse(BaseModel):
    session_id: str
    stored: bool = True


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class SessionSnapshot(BaseModel):
    session_id: str
    context: AnalysisContext
    messages: List[dict]


class ResetRequest(BaseModel):
    session_id: str
    mode: Literal["history", "all"] = "history"  # history: keep context, all: remove session entirely

