from enum import Enum


class Scenario(Enum):
    INTERVIEW = (
        "面试",
        "你是一位面试官，用英语进行技术面试，每次问一个问题，等用户回答后再继续",
        "I'm ready for the interview. Please start.",
    )
    FRIEND_CHAT = (
        "朋友聊天",
        "你是一位友善的英语母语者，和用户聊日常话题，像朋友一样自然对话",
        "Hi! How are you doing today?",
    )
    ASKING_HELP = (
        "求助",
        "你是商店店员，顾客（用户）需要帮助，用清晰简单的英语提供帮助",
        "Hello, I need some help please.",
    )

    def __init__(self, label: str, prompt: str, initial_message: str):
        self.label = label
        self.prompt = prompt
        self.initial_message = initial_message

    def __str__(self):
        return self.label
