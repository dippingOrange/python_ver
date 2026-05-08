import json
import random
from pathlib import Path
from typing import Optional
from model.reading_result import ReadingResult
from model.pronunciation_result import PronunciationResult, WordScore
from service.ai_service import AiService
from service.alibaba_asr_service import AlibabaAsrService


class ReadingService:
    TEXTS_FILE = "texts.txt"

    def __init__(self, ai_service: AiService, alibaba_asr: AlibabaAsrService):
        self.ai_service = ai_service
        self.alibaba_asr = alibaba_asr

    def get_random_passage(self) -> Optional[str]:
        path = Path(self.TEXTS_FILE)
        if not path.exists():
            return None

        passages = []
        current = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                current.append(line.strip())
            else:
                if current:
                    passages.append(" ".join(current))
                    current = []
        if current:
            passages.append(" ".join(current))

        if not passages:
            return None
        return random.choice(passages)

    def evaluate(self, passage: str, user_input: str, wav_path: Optional[str] = None) -> ReadingResult:
        # 1. Pronunciation assessment (if audio available and Alibaba enabled)
        pron_result = None
        if wav_path and Path(wav_path).exists() and self.alibaba_asr.is_enabled():
            pron_result = self.alibaba_asr.evaluate(wav_path, passage)

        # 2. Build prompt with objective data for coaching
        system_prompt = self._build_system_prompt(pron_result)
        user_message = f"Passage: {passage}\n\nMy reading: {user_input}"

        # 3. Call DeepSeek
        response = self.ai_service.call_api(system_prompt, user_message)

        # 4. Parse AI response
        result = self._parse_ai_response(response)

        # 5. Merge pronunciation data
        if pron_result is not None:
            result.pronunciation_score = pron_result.pronunciation_score
            result.fluency_score = pron_result.fluency_score
            result.completeness_score = pron_result.completeness_score
            result.word_scores = pron_result.word_scores

        return result

    def _build_system_prompt(self, pron_result: Optional[PronunciationResult]) -> str:
        parts = ["You are an English pronunciation coach."]

        if pron_result is not None:
            parts.append("\nAcoustic pronunciation assessment (Alibaba Cloud):")
            parts.append(f"- Pronunciation score: {pron_result.pronunciation_score}/100")
            parts.append(f"- Fluency: {pron_result.fluency_score}/100")
            parts.append(f"- Completeness: {pron_result.completeness_score}/100")

            if pron_result.word_scores:
                weak_words = [w.word for w in pron_result.word_scores if w.score < 80]
                if weak_words:
                    parts.append(f"- Words needing attention: {' '.join(weak_words)}")
            parts.append("Use this objective data to give targeted coaching advice.")

        parts.append(' Return JSON only: {"score": <0-100>, "feedback": "...", "tips": "..."}')
        return "\n".join(parts)

    def _parse_ai_response(self, response: str) -> ReadingResult:
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end > start:
            json_str = response[start : end + 1]
            try:
                data = json.loads(json_str)
                result = ReadingResult()
                result.score = data.get("score", 0)
                result.feedback = data.get("feedback", "")
                result.tips = data.get("tips", "")
                return result
            except (json.JSONDecodeError, KeyError):
                pass

        result = ReadingResult()
        result.score = 0
        result.feedback = response
        result.tips = "Could not parse structured result."
        return result
