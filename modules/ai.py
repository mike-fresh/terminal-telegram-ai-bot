import openai
from modules.message import OpenAIMessage
from modules.config import Config


class ChatPartner:
    def __init__(self):
        self.config = Config()

    def talk_to_openai(self, messages: list[OpenAIMessage], response_max_tokens: int) -> dict:
        response: dict = self._get_openai_response(messages, response_max_tokens)
        return response

    def _get_openai_response(self, messages: list[OpenAIMessage], max_tokens: int) -> dict:
        return openai.ChatCompletion.create(
            model=self.config.MODEL,
            messages=[msg.to_dict() for msg in messages],
            temperature=self.config.TEMPERATURE,
            max_tokens=max_tokens
        )
