from dataclasses import dataclass


@dataclass
class ConversationTurn:
    user_text: str
    pronunciation_score: int = -1
    ai_response: str = ""
