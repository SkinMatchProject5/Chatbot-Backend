Chatbot Backend (FastAPI)

Overview
- Purpose: Hold analysis context (diagnosis, summary, similar diseases, refined symptoms) in a per-session memory and answer user questions using OpenAI.
- Tech: FastAPI, Pydantic, OpenAI Python SDK, in-memory session store (pluggable to Redis later).

Run
- Python 3.10+
- pip install -r requirements.txt
- Create .env from .env.example and set OPENAI_API_KEY
- Start: uvicorn app.main:app --reload --port 8010

Env (.env)
- OPENAI_API_KEY=
- MODEL=gpt-4o-mini
- LOG_LEVEL=info
- HOST=0.0.0.0
- PORT=8010
- ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

API
1) POST /api/v1/session/init
   - Body: { diagnosis, summary, similar_diseases, refined_symptoms }
   - Returns: { session_id, stored: true }
   - Purpose: Preload analysis result so bot remembers.

2) POST /api/v1/chat
   - Body: { session_id, message }
   - Returns: { reply, session_id }
   - Uses system prompt + stored analysis context + prior turns to call OpenAI.

3) GET /api/v1/session/{id}
   - Returns: { session_id, context, messages }

4) POST /api/v1/session/reset
   - Body: { session_id }
   - Clears message history but keeps analysis context.

5) POST /api/v1/session/init-from-analysis
   - Body: Raw analysis JSON (from AI-Analysis-Backend SkinDiagnosisResponse or frontend-transformed result)
   - Returns: { session_id }
   - Auto-maps keys: diagnosis|predicted_disease, recommendations|summary, metadata.similar_diseases_scored, similar_diseases, similar_conditions, refined_text.

6) POST /api/v1/session/append-context
   - Query: session_id
   - Body: { diagnosis?, summary?, refined_symptoms?, similar_diseases?[] }
   - Merges/updates context fields without clearing history.

7) POST /api/v1/consult/start
   - Body: { analysis: <SkinDiagnosisResponse-like JSON>, message?: string }
   - Returns: { session_id, reply }
   - One-call bootstrap: creates session from analysis and optionally answers the first question.

8) POST /api/v1/consult/message
   - Body: { session_id: string, message: string }
   - Returns: { session_id, reply }
   - Convenience wrapper around /chat.

Context mapping from analysis backend
- diagnosis: SkinDiagnosisResponse.diagnosis
- summary: SkinDiagnosisResponse.recommendations (or summary derived)
- similar_diseases: SkinDiagnosisResponse.metadata.similar_diseases_scored[] (fallback to similar_conditions string)
- refined_symptoms: UtteranceRefineResponse.refined_text

Frontend integration
- Add VITE_CHATBOT_API_BASE_URL (e.g., http://localhost:8010)
- On analysis completion, call /session/init once and keep session_id in client state.
- Route user questions to /chat with session_id.
- Alternatively, pass raw analysis to /session/init-from-analysis for convenience.

Security
- For MVP, public endpoints with CORS; later add JWT (Authorization: Bearer) to align with auth server.

Health
- GET /health → { status: "ok", service: "chatbot" }
