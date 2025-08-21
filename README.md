# AI 피부 진단 챗봇 백엔드 (FastAPI)

## 개요
- **목적**: 피부 분석 결과(진단, 요약, 유사 질환, 정제된 증상)를 세션별 메모리에 저장하고 OpenAI를 활용하여 사용자 질문에 답변
- **기술 스택**: FastAPI, Pydantic, OpenAI Python SDK, 인메모리 세션 저장소 (추후 Redis 연동 가능)

## 실행 방법
```bash
# 필요 조건: Python 3.10+
pip install -r requirements.txt

# .env.example을 참고하여 .env 파일 생성 후 OPENAI_API_KEY 설정
cp .env.example .env

# 서버 시작
uvicorn app.main:app --reload --port 8010
```

## 환경변수 설정 (.env)
```
OPENAI_API_KEY=your_openai_api_key_here
MODEL=gpt-4o-mini
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8010
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## API 엔드포인트

### 1) 세션 초기화
**POST** `/api/v1/session/init`
- **요청**: `{ diagnosis, summary, similar_diseases, refined_symptoms }`
- **응답**: `{ session_id, stored: true }`
- **목적**: 분석 결과를 미리 로드하여 챗봇이 기억하도록 함

### 2) 채팅
**POST** `/api/v1/chat`
- **요청**: `{ session_id, message }`
- **응답**: `{ reply, session_id }`
- **기능**: 시스템 프롬프트 + 저장된 분석 컨텍스트 + 이전 대화를 사용하여 OpenAI 호출

### 3) 세션 조회
**GET** `/api/v1/session/{id}`
- **응답**: `{ session_id, context, messages }`

### 4) 세션 리셋
**POST** `/api/v1/session/reset`
- **요청**: `{ session_id }`
- **기능**: 메시지 기록은 지우지만 분석 컨텍스트는 유지

### 5) 분석 결과로 세션 초기화
**POST** `/api/v1/session/init-from-analysis`
- **요청**: AI-Analysis-Backend의 SkinDiagnosisResponse 또는 프론트엔드 변환 결과 JSON
- **응답**: `{ session_id }`
- **기능**: 자동 키 매핑 (diagnosis|predicted_disease, recommendations|summary 등)

### 6) 컨텍스트 추가
**POST** `/api/v1/session/append-context`
- **쿼리**: `session_id`
- **요청**: `{ diagnosis?, summary?, refined_symptoms?, similar_diseases?[] }`
- **기능**: 기록을 지우지 않고 컨텍스트 필드 병합/업데이트

### 7) 상담 시작
**POST** `/api/v1/consult/start`
- **요청**: `{ analysis: <SkinDiagnosisResponse 형태 JSON>, message?: string }`
- **응답**: `{ session_id, reply }`
- **기능**: 원스톱 부트스트랩 - 분석으로부터 세션 생성 및 선택적 첫 질문 답변

### 8) 상담 메시지
**POST** `/api/v1/consult/message`
- **요청**: `{ session_id: string, message: string }`
- **응답**: `{ session_id, reply }`
- **기능**: /chat의 편의 래퍼

## 분석 백엔드 컨텍스트 매핑
- `diagnosis`: SkinDiagnosisResponse.diagnosis
- `summary`: SkinDiagnosisResponse.recommendations (또는 파생된 요약)
- `similar_diseases`: SkinDiagnosisResponse.metadata.similar_diseases_scored[] (similar_conditions 문자열로 폴백)
- `refined_symptoms`: UtteranceRefineResponse.refined_text

## 프론트엔드 연동
- `VITE_CHATBOT_API_BASE_URL` 환경변수 추가 (예: http://localhost:8010)
- 분석 완료 시 `/session/init`을 한 번 호출하고 클라이언트 상태에 session_id 보관
- 사용자 질문을 session_id와 함께 `/chat`으로 라우팅
- 또는 편의를 위해 원시 분석 데이터를 `/session/init-from-analysis`로 전달

## 보안
- MVP용으로 CORS가 적용된 공개 엔드포인트 제공
- 추후 인증 서버와 연동하여 JWT (Authorization: Bearer) 추가 예정

## 헬스체크
**GET** `/health` → `{ status: "ok", service: "chatbot" }`
