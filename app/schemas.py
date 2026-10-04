from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Article(BaseModel):
    title: str
    url: HttpUrl
    published_at: datetime | None = None
    author: str | None = None
    content: str = ""
    source: str
    credibility_score: int | None = Field(default=None, ge=0, le=100)
    credibility_reason: str | None = None
    truth_score: int | None = Field(default=None, ge=0, le=100)
    confidence: int | None = Field(default=None, ge=0, le=100)
    truth_label: Literal["Likely True", "Possibly True", "Needs Verification", "Likely False"] | None = None
    truth_reason: str | None = None
    is_technology: bool | None = None
    category: str | None = None
    ai_summary: str | None = None


class ValidationResult(BaseModel):
    article: Article
    credibility_score: int = Field(ge=0, le=100)
    reasons: list[str]


class KnowledgeItem(BaseModel):
    topic: str
    category: str
    companies: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    important_events: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    article_url: str


class TrendReport(BaseModel):
    most_mentioned_companies: list[tuple[str, int]] = Field(default_factory=list)
    most_mentioned_technologies: list[tuple[str, int]] = Field(default_factory=list)
    most_discussed_frameworks: list[tuple[str, int]] = Field(default_factory=list)
    article_count: int = 0


class SummaryReport(BaseModel):
    markdown: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
