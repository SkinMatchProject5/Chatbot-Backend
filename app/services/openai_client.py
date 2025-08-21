from typing import List, Dict
from openai import OpenAI
from app.core.config import settings


def build_system_prompt() -> str:
    return (
        "너는 환자의 이미징/문장 분석 결과를 바탕으로, 결과를 이해하기 쉽게 설명하고, "
        "생활 관리와 다음 단계(의료진 상담 포함)를 안내하는 도우미야. "
        "진단을 단정하거나 치료를 지시하지 말고, 의료 면책 고지를 덧붙여. "
        "사용자가 새로운 증상을 제시하면 결과와 일치/불일치를 설명하되, 재진단은 하지 마."
    )


def build_context_message(ctx: Dict) -> Dict:
    # 구조화된 JSON 컨텍스트를 system 보조 메시지로 제공
    content = (
        "다음은 분석 백엔드에서 제공한 컨텍스트야:\n" 
        f"- 질환명: {ctx.get('diagnosis','')}\n"
        f"- 소견: {ctx.get('summary','')}\n"
        f"- 유사질환: {', '.join(ctx.get('similar_diseases', []) or [])}\n"
        f"- 증상정리: {ctx.get('refined_symptoms','')}\n"
        "이 컨텍스트를 대화 전반에 참고해."
    )
    return {"role": "system", "content": content}


def chat_completion(messages: List[Dict]) -> str:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=settings.MODEL,
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""

