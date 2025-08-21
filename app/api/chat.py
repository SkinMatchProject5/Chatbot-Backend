from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.schemas import (
    InitSessionRequest, InitSessionResponse,
    ChatRequest, ChatResponse,
    SessionSnapshot, ResetRequest, AnalysisContext,
)
from app.services.memory import memory_store
from app.services.openai_client import build_system_prompt, build_context_message, chat_completion
from app.services.context_mapper import map_to_context


router = APIRouter()


@router.post("/session/init", response_model=InitSessionResponse)
def init_session(req: InitSessionRequest):
    try:
        ctx = AnalysisContext(
            diagnosis=req.diagnosis,
            summary=req.summary,
            similar_diseases=req.similar_diseases or [],
            refined_symptoms=req.refined_symptoms,
        )
        sess = memory_store.create(ctx)
        return InitSessionResponse(session_id=sess.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/init-from-analysis", response_model=InitSessionResponse)
def init_from_analysis(payload: Dict[str, Any]):
    """Initialize session by passing raw analysis payload from AI-Analysis-Backend or frontend.

    Accepts flexible keys (diagnosis, recommendations/summary, similar_* variants, refined_text...)
    """
    try:
        ctx = map_to_context(payload)
        sess = memory_store.create(ctx)
        return InitSessionResponse(session_id=sess.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid analysis payload: {e}")


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    sess = memory_store.get(req.session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    # Build message list: system + context + history + user
    messages: List[dict] = []
    messages.append({"role": "system", "content": build_system_prompt()})
    messages.append(build_context_message(sess.context.model_dump()))
    messages.extend(sess.messages)
    messages.append({"role": "user", "content": req.message})

    reply = chat_completion(messages)

    # persist turn
    memory_store.add_message(req.session_id, "user", req.message)
    memory_store.add_message(req.session_id, "assistant", reply)

    return ChatResponse(session_id=req.session_id, reply=reply)


@router.get("/session/{session_id}", response_model=SessionSnapshot)
def get_session(session_id: str):
    sess = memory_store.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    return SessionSnapshot(session_id=sess.id, context=sess.context, messages=sess.messages)


@router.post("/session/reset")
def reset_session(req: ResetRequest):
    if req.mode == "all":
        memory_store.delete(req.session_id)
        return {"deleted": True}
    memory_store.reset_history(req.session_id)
    return {"history_cleared": True}


@router.post("/session/append-context")
def append_context(session_id: str, patch: Dict[str, Any]):
    """Append/merge additional context fields (e.g., add refined_symptoms later).

    - Only updates known fields; history untouched.
    """
    sess = memory_store.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")
    try:
        if "diagnosis" in patch and str(patch["diagnosis"]).strip():
            sess.context.diagnosis = str(patch["diagnosis"]).strip()
        if "summary" in patch and patch["summary"] is not None:
            sess.context.summary = str(patch["summary"]) if patch["summary"] != "" else None
        if "refined_symptoms" in patch and patch["refined_symptoms"] is not None:
            sess.context.refined_symptoms = str(patch["refined_symptoms"]) if patch["refined_symptoms"] != "" else None
        # Merge similar diseases if provided
        sim = patch.get("similar_diseases")
        if isinstance(sim, list):
            merged = list(dict.fromkeys([*sess.context.similar_diseases, *[str(s).strip() for s in sim if str(s).strip()]]))
            sess.context.similar_diseases = merged
        return {"updated": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid patch: {e}")


@router.post("/consult/start")
def consult_start(payload: Dict[str, Any]):
    """Convenience endpoint: create session from analysis and optionally answer first question.

    Body example:
    {
      "analysis": { ... SkinDiagnosisResponse-like ... },
      "message": "첫 질문 내용"  # optional
    }
    """
    try:
        analysis = payload.get("analysis") or {}
        message = payload.get("message")
        # init session from analysis
        ctx = map_to_context(analysis)
        sess = memory_store.create(ctx)

        if not message:
            # Return a friendly greeting that summarizes the context
            greeting = (
                f"분석 결과는 '{ctx.diagnosis}'로 보이며, 궁금한 점을 물어보세요. "
                f"유사질환: {', '.join(ctx.similar_diseases) if ctx.similar_diseases else '없음'}."
            )
            memory_store.add_message(sess.id, "assistant", greeting)
            return {"session_id": sess.id, "reply": greeting}

        # Otherwise answer the user message
        messages: List[dict] = []
        messages.append({"role": "system", "content": build_system_prompt()})
        messages.append(build_context_message(sess.context.model_dump()))
        messages.append({"role": "user", "content": message})
        reply = chat_completion(messages)
        memory_store.add_message(sess.id, "user", message)
        memory_store.add_message(sess.id, "assistant", reply)
        return {"session_id": sess.id, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/consult/message")
def consult_message(payload: Dict[str, Any]):
    """Convenience endpoint: send a message in an existing session.

    Body: { session_id, message }
    """
    sid = payload.get("session_id")
    msg = payload.get("message")
    if not sid or not msg:
        raise HTTPException(status_code=400, detail="session_id and message are required")

    sess = memory_store.get(sid)
    if not sess:
        raise HTTPException(status_code=404, detail="session not found")

    messages: List[dict] = []
    messages.append({"role": "system", "content": build_system_prompt()})
    messages.append(build_context_message(sess.context.model_dump()))
    messages.extend(sess.messages)
    messages.append({"role": "user", "content": msg})
    reply = chat_completion(messages)
    memory_store.add_message(sid, "user", msg)
    memory_store.add_message(sid, "assistant", reply)
    return {"session_id": sid, "reply": reply}
