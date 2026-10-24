from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    force_demo_mode: bool
    demo_fixed_answer: bool
    deepseek_configured: bool
    qwen_configured: bool


class RecognitionRequest(BaseModel):
    filename: str = "unknown.jpg"


class RecognitionCandidate(BaseModel):
    name: str
    confidence: float
    symptoms: str = ""
    causes: str = ""


class RecognitionEvidence(BaseModel):
    source: str = ""
    text: str = ""
    score: float = 0.0


class RecognitionResponse(BaseModel):
    primary: RecognitionCandidate
    top_candidates: List[RecognitionCandidate]
    model_used: str
    rag_evidence: List[RecognitionEvidence]
    confidence: float
    symptoms: str
    lesion_description: str


class ChatMessageReq(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    history: Optional[List[ChatMessageReq]] = None
    force_fixed_answer: Optional[bool] = False


class ChatCitation(BaseModel):
    rank: int
    source: str = ""
    score: float = 0.0
    chunk_text: str = ""


class ChatResponse(BaseModel):
    answer: str
    citations: List[ChatCitation]
    has_evidence: bool
    retrieval_score: float
    model_used: str
    session_id: Optional[str] = None


class DocListResponse(BaseModel):
    id: int
    filename: str
    doc_type: str
    chunk_count: int
    status: str
    file_size: int = 0
    created_at: Optional[datetime] = None


class DocIndexResponse(BaseModel):
    status: str
    chunk_count: int = 0
    error: Optional[str] = None


class PlanMedication(BaseModel):
    drug: str = ""
    dosage: str = ""
    frequency: str = ""
    precautions: str = ""


class PlanFertilization(BaseModel):
    type: str = ""
    dosage: str = ""
    timing: str = ""


class PlanEvidence(BaseModel):
    source: str = ""
    citation: str = ""
    score: float = 0.0


class PlanGenerateRequest(BaseModel):
    disease_name: str
    symptoms: str = ""


class PlanGenerateResponse(BaseModel):
    plan_title: str
    medication_plan: List[PlanMedication]
    fertilization_plan: List[PlanFertilization]
    prevention_tips: str = ""
    agricultural_operations: str = ""
    rag_evidence: List[PlanEvidence] = []
    model_used: str = ""


class PlanExportResponse(BaseModel):
    file_path: str
    filename: str
    file_size: int


class StatsOverview(BaseModel):
    total_recognitions: int
    total_chats: int
    total_documents: int
    total_plans: int
    top_diseases: List[Dict[str, Any]]


class DiseaseDictItem(BaseModel):
    id: int
    name: str
    alias: Optional[str] = None
    crop_type: str = "玉米"
    severity: Optional[str] = None
