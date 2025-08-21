from typing import Any, Dict, List
from app.models.schemas import AnalysisContext


def _extract_similar(payload: Dict[str, Any]) -> List[str]:
    # 1) metadata.similar_diseases_scored -> [ {name, score} ]
    md = payload.get("metadata") or {}
    scored = md.get("similar_diseases_scored")
    if isinstance(scored, list) and scored:
        names = []
        for item in scored:
            try:
                name = str(item.get("name", "")).strip()
                if name:
                    names.append(name)
            except Exception:
                continue
        if names:
            return names

    # 2) similar_diseases: list of {name, ...} or list[str]
    sd = payload.get("similar_diseases")
    if isinstance(sd, list) and sd:
        names = []
        for item in sd:
            if isinstance(item, str):
                if item.strip():
                    names.append(item.strip())
            elif isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    names.append(name)
        if names:
            return names

    # 3) similar_conditions: comma-separated string
    sc = payload.get("similar_conditions")
    if isinstance(sc, str) and sc.strip():
        return [s.strip() for s in sc.split(',') if s.strip()]

    return []


def map_to_context(payload: Dict[str, Any]) -> AnalysisContext:
    # Accepts SkinDiagnosisResponse-like or frontend-transformed payloads
    diagnosis = (
        payload.get("diagnosis")
        or payload.get("predicted_disease")
        or "분석 결과 없음"
    )
    summary = payload.get("recommendations") or payload.get("summary")
    refined_symptoms = (
        payload.get("refined_symptoms")
        or payload.get("refined_text")
        or None
    )
    similar = _extract_similar(payload)

    return AnalysisContext(
        diagnosis=str(diagnosis),
        summary=str(summary) if summary is not None else None,
        similar_diseases=similar,
        refined_symptoms=str(refined_symptoms) if refined_symptoms is not None else None,
    )

