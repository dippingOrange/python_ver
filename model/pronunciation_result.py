from dataclasses import dataclass, field
from typing import List


@dataclass
class PhonemeScore:
    phoneme: str = ""
    score: int = -1


@dataclass
class WordScore:
    word: str = ""
    score: int = -1
    phoneme_scores: List[PhonemeScore] = field(default_factory=list)


@dataclass
class PronunciationResult:
    overall_score: int = -1
    pronunciation_score: int = -1
    fluency_score: int = -1
    completeness_score: int = -1
    word_scores: List[WordScore] = field(default_factory=list)
