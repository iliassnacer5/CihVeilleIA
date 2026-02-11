from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Document(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    text: str


class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5


class RagAnswer(BaseModel):
    question: str
    answer: str
    context: List[str]


class ChatSource(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    score: float


class ChatRequest(BaseModel):
    question: str
    top_k: int = 5
    lang: Optional[str] = None


class ChatAnswer(BaseModel):
    question: str
    answer: str
    safe: bool
    reason: str
    sources: List[ChatSource]


# --- New Schemas for React Integration ---

class KpiResponse(BaseModel):
    monitored_sources: int
    documents_month: int
    regulatory_updates: int
    ai_processing_rate: float
    avg_processing_time: str
    system_health: str


class ChartDataItem(BaseModel):
    month: str
    documents: int
    alerts: int


class ThemeDistributionItem(BaseModel):
    name: str
    value: int


class DashboardAnalytics(BaseModel):
    documents_over_time: List[ChartDataItem]
    distribution_by_theme: List[ThemeDistributionItem]


class AlertItem(BaseModel):
    id: str
    title: str
    description: str
    source: str
    severity: str
    category: str
    timestamp: str
    read: bool


class DocumentListItem(BaseModel):
    id: str
    title: str
    source: str
    date: str
    theme: str
    confidence: int
    url: Optional[str] = None


class DocumentDetail(BaseModel):
    id: str
    title: str
    source: str
    date: str
    theme: str
    confidence: int
    url: Optional[str] = None
    summary: str
    entities: List[str]
    content: str


class SummarizeResponse(BaseModel):
    id: str
    summary: str
    topics: List[str]
    entities: List[str]
    confidence: int
    key_facts: List[str]


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str


class AuditLog(BaseModel):
    id: str
    timestamp: str
    user: str
    action: str
    module: str
    status: str
    details: str


class WhitelistedDomain(BaseModel):
    id: int
    domain: str
    addedDate: str


class AppSettings(BaseModel):
    refreshFrequency: str
    confidenceThreshold: int
    dataRetentionDays: int
    enableNotifications: bool


class SourceSchema(BaseModel):
    id: Optional[str] = None
    name: str
    url: str
    type: str
    frequency: str
    status: str = "Active"
    lastUpdated: str = "Never"

