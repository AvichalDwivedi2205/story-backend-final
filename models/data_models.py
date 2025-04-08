from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class JournalEntry(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str


class SentimentAnalysis(BaseModel):
    score: float
    label: str


class EmotionAnalysis(BaseModel):
    emotions: Dict[str, float]
    dominant_emotion: str


class JournalInsight(BaseModel):
    summary: str
    key_themes: List[str]
    cognitive_distortions: List[str]
    growth_indicators: List[str]
    reflection_questions: List[str]
    actionable_advice: List[str]


class JournalAnalysis(BaseModel):
    journal_entry: JournalEntry
    sentiment_analysis: SentimentAnalysis
    emotion_analysis: EmotionAnalysis
    insights: JournalInsight


class Exercise(BaseModel):
    text: str
    completed: bool = False


class Exercises(BaseModel):
    morning_reflection: Exercise
    gratitude_exercise: Exercise
    mindfulness_meditation: Exercise
    cbt_exercise: Exercise
    relaxation_techniques: Exercise


class TherapyMessage(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_user: bool


class TherapySession(BaseModel):
    messages: List[TherapyMessage]
    session_summary: Optional[str] = None
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentResponse(BaseModel):
    success: bool
    data: Any
    message: str