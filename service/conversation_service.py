from pathlib import Path
from typing import Optional
from model.scenario import Scenario
from model.conversation_turn import ConversationTurn
from service.ai_service import AiService
from service.alibaba_asr_service import AlibabaAsrService


class ConversationService:
    LENGTH_NORMAL = 0
    LENGTH_DETAILED = 1
    LENGTH_LABELS = ["Normal", "Detailed"]

    def __init__(self, ai_service: AiService, alibaba_asr: AlibabaAsrService):
        self.ai_service = ai_service
        self.alibaba_asr = alibaba_asr
        self.current_scenario: Optional[Scenario] = None
        self.response_length = self.LENGTH_NORMAL
        self.turns: list = []

    def set_response_length(self, length: int):
        self.response_length = length

    def set_scenario(self, scenario: Scenario):
        self.current_scenario = scenario

    def _build_prompt(self) -> str:
        if self.current_scenario is None:
            raise RuntimeError("No scenario selected")
        base = self.current_scenario.prompt
        if self.response_length == self.LENGTH_DETAILED:
            return (
                base
                + "\nGive detailed responses (4-6 sentences). Ask follow-up questions. Provide rich descriptions and examples."
            )
        return base + "\nKeep responses concise (2-3 sentences)."

    def send_message(self, user_input: str, wav_path: Optional[str] = None) -> str:
        pron_score = -1

        if wav_path and Path(wav_path).exists() and self.alibaba_asr.is_enabled():
            result = self.alibaba_asr.evaluate(wav_path, user_input)
            if result is not None:
                pron_score = result.pronunciation_score

        ai_response = self.ai_service.call_api(self._build_prompt(), user_input)
        self.turns.append(ConversationTurn(user_input, pron_score, ai_response))
        return ai_response

    def start_conversation(self) -> str:
        if self.current_scenario is None:
            raise RuntimeError("No scenario selected")
        return self.ai_service.call_api(
            self._build_prompt(), self.current_scenario.initial_message
        )

    def get_conversation_summary(self) -> str:
        if not self.turns:
            return "No conversation data to summarize."

        turn_data_parts = []
        total_score = 0
        scored_turns = 0

        for i, turn in enumerate(self.turns):
            parts = [f'Turn {i + 1}: "{turn.user_text}"']
            if turn.pronunciation_score >= 0:
                parts.append(f" [Pronunciation: {turn.pronunciation_score}/100]")
                total_score += turn.pronunciation_score
                scored_turns += 1
            parts.append(f"\n  AI: {turn.ai_response}\n")
            turn_data_parts.append("".join(parts))

        avg_score = (
            f"{total_score // scored_turns}"
            if scored_turns > 0
            else "N/A (no voice input)"
        )

        system_prompt = (
            "You are an English pronunciation coach. "
            "A student just completed a conversation practice session. "
            "Below is the conversation log with pronunciation scores from Alibaba Cloud speech assessment. "
            "Provide: 1) Overall pronunciation assessment, "
            "2) 2-3 specific tips for improvement, "
            "3) An encouraging closing message. "
            "Keep it 3-5 sentences, conversational and supportive."
        )

        user_message = (
            f"Average pronunciation score: {avg_score}/100\n\n"
            f"Conversation log:\n{chr(10).join(turn_data_parts)}"
        )

        return self.ai_service.call_api(system_prompt, user_message)

    def reset(self):
        self.turns.clear()

    def has_scored_turns(self) -> bool:
        return any(t.pronunciation_score >= 0 for t in self.turns)
