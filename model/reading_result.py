from dataclasses import dataclass, field
from typing import List
from .pronunciation_result import WordScore


@dataclass
class ReadingResult:
    score: int = 0
    feedback: str = ""
    tips: str = ""
    pronunciation_score: int = -1
    fluency_score: int = -1
    completeness_score: int = -1
    word_scores: List[WordScore] = field(default_factory=list)
