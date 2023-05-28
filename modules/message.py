import tiktoken
from modules.config import Config


class OpenAIMessage:
    config: Config = Config()

    def __init__(self, content: str, sender: str, receiver: str,
                 role: str, category: str, chat_id: str, token_count: int = 0) -> None:
        self.content: str = content
        self.sender: str = sender
        self.receiver: str = receiver
        self.role: str = role
        self.category: str = category
        self.chat_id: str = chat_id
        self.token_count: int = token_count
        if self.token_count == 0:
            self.set_token_count()

    def calculate_token(self) -> int:
        encoding = tiktoken.encoding_for_model(self.config.MODEL)
        num_token = len(encoding.encode(self.content))
        return num_token

    def set_token_count(self) -> None:
        self.token_count = self.calculate_token()

    def is_too_long(self) -> bool:
        return self.token_count > self.config.MAX_TOKENS

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "name": self.sender
        }

    def __str__(self):
        return self.content

    def __repr__(self):
        return f"OpenAIMessage: sender={self.sender}, receiver={self.receiver}, " \
               f"role={self.role}, category={self.category}, chat_id={self.chat_id}, content={self.content[:12]}"
