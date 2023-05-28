from modules.config import Config
from modules.message import OpenAIMessage
from modules.database import Database
from modules.tools import clean_username
import datetime


class Conversation:
    config = Config()
    db = Database(config.DB_URI)

    def __init__(self, chat_id: str, username: str) -> None:
        self.chat_id: str = chat_id
        self.username: str = clean_username(username)
        self.config_messages: list[OpenAIMessage] = []
        self.user_messages: list[OpenAIMessage] = []
        self.conversation_start_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                                        f"{self.config.CONVERSATION_START_LOG_MSG} "
                                                        f"{self.username}"
                                                        f"{self.config.LOG_MSG_APPENDIX}",
                                                        'system', 'system', 'system', 'log', self.chat_id)
        self.conversation_reset_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                                        f"{self.config.CONVERSATION_RESET_LOG_MSG} "
                                                        f"{self.username}"
                                                        f"{self.config.LOG_MSG_APPENDIX}",
                                                        'system', 'system', 'system', 'log', self.chat_id)
        self.setup_config_messages()
        self.setup_user_messages()

    @property
    def full_messages(self) -> list[OpenAIMessage]:
        return self.config_messages + self.user_messages

    @property
    def config_messages_count(self) -> int:
        return len(self.config_messages)

    @property
    def user_messages_count(self) -> int:
        return len(self.user_messages)

    @property
    def total_messages_count(self) -> int:
        return self.config_messages_count + self.user_messages_count

    @property
    def config_tokens(self) -> int:
        return sum([msg.token_count for msg in self.config_messages])

    @property
    def user_tokens(self) -> int:
        return sum([msg.token_count for msg in self.user_messages])

    @property
    def total_tokens(self) -> int:
        return self.config_tokens + self.user_tokens

    @property
    def exists(self) -> bool:
        return self.db.check_conversation_exists(self.chat_id)

    def add_message(self, message: OpenAIMessage, logging: bool = True) -> None:
        self.username = message.sender
        self.user_messages.append(message)
        self.message_log(message)
        if logging:
            self.system_log(message)

    def remove_last_message(self, logging: bool = True) -> None:
        if self.user_messages_count == 0:
            return
        self.user_messages.pop()
        self.db.remove_last_message(self.chat_id)
        if logging:
            self.system_log(OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                          f"{self.config.REMOVE_LAST_MESSAGE_LOG_MSG} "
                                          f"{self.config.LOG_MSG_APPENDIX}",
                                          'system', 'system', 'system', 'log', self.chat_id))

    def setup_config_messages(self, logging: bool = True) -> None:
        if self.db.check_config_exists(self.chat_id):
            self.config_messages = self.db.get_conversation_from_db(self.chat_id, category='config')
            return
        self.config_messages = [
            OpenAIMessage(self.config.SYSTEM_PROMPT.format(name=self.config.NAME),
                          self.config.NAME, self.config.NAME, 'system', 'config', self.chat_id),
            OpenAIMessage(self.config.MY_NAME_IS + ' ' + self.username.replace("_", " "),
                          self.username, self.config.NAME, 'user', 'config', self.chat_id),
            OpenAIMessage(f'{self.config.I_WILL_CALL_YOU} {self.username.split("_", 1)[0]}',
                          self.config.NAME, self.username, 'assistant', 'config', self.chat_id),
        ]
        for msg in self.config_messages:
            self.message_log(msg)
        if logging:
            self.system_log(self.conversation_start_log_msg)

    def setup_user_messages(self) -> None:
        self.user_messages = self.db.get_conversation_from_db(self.chat_id, category='user')

    def create_openai_response_message(self, response: dict):
        response_content = response["choices"][0]["message"]["content"]
        return OpenAIMessage(response_content, self.config.NAME, self.username, 'assistant', 'user', self.chat_id)

    def message_log(self, message: OpenAIMessage):
        self.db.add_message_to_messages(message.content, message.sender, message.receiver,
                                        message.role, message.category, message.chat_id,
                                        message.token_count, datetime.datetime.now())

    def system_log(self, message: OpenAIMessage):
        self.db.add_message_to_system_log(message.content, message.sender, message.receiver,
                                          message.role, message.category, message.chat_id,
                                          message.token_count, datetime.datetime.now())

    def clear_messages(self, logging=True) -> None:
        self.user_messages.clear()
        self.db.remove_conversation(self.chat_id)
        if logging:
            self.system_log(self.conversation_reset_log_msg)
