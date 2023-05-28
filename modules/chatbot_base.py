import datetime
from modules.database import Database
from modules.message import OpenAIMessage
from modules.config import Config
from modules.tools import clean_username
from modules.conversation import Conversation
from modules.ai import ChatPartner


class ChatBot:
    def __init__(self) -> None:
        super().__init__()
        self.config: Config = Config()
        self.LOCAL_USERNAME: str = clean_username(self.config.LOCAL_USERNAME)
        self.db = Database(self.config.DB_URI)
        self.chatpartner = ChatPartner()
        self.start_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                           f"{self.config.NAME} "
                                           f"{self.config.START_LOG_MSG}"
                                           f"{self.config.LOG_MSG_APPENDIX}",
                                           'system', 'system', 'system', 'log', 'system_log')
        self.stop_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                          f"{self.config.NAME} "
                                          f"{self.config.STOP_LOG_MSG}"
                                          f"{self.config.LOG_MSG_APPENDIX}",
                                          'system', 'system', 'system', 'log', 'system_log')
        self._log_message(self.start_log_msg)

    def process_message(self, message: OpenAIMessage) -> OpenAIMessage:
        conversation: Conversation = Conversation(message.chat_id, message.sender)
        conversation.add_message(message)
        try:
            response: dict = self.chatpartner.talk_to_openai(conversation.full_messages, self.config.MAX_TOKENS)
            response_message: OpenAIMessage = conversation.create_openai_response_message(response)
            response_message.token_count = response["usage"]["completion_tokens"]
            conversation.add_message(response_message)
        except Exception as e:
            conversation.remove_last_message()
            response_message = self._handle_error(message, e)
        return response_message

    def _handle_error(self, message: OpenAIMessage, error: Exception) -> OpenAIMessage:
        error_message = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                      f"{self.config.ERROR_LOG_MSG}"
                                      f"{self.config.LOG_MSG_APPENDIX} "
                                      f"{self.config.LOG_MSG_PREFIX} "
                                      f"{error} ",
                                      'system', 'system', 'system', 'log', message.chat_id)
        self._log_message(error_message)
        return error_message

    def _log_message(self, message: OpenAIMessage):
        self.db.add_message_to_system_log(message.content, message.sender, message.receiver,
                                          message.role, message.category, message.chat_id,
                                          message.token_count, datetime.datetime.now())

    def _start_conversation(self, message: OpenAIMessage, logging: bool = True) -> None:
        msg_list = self._create_start_messages(message)
        for msg in msg_list:
            self.db.add_message_to_messages(msg.content, msg.sender, msg.receiver,
                                            msg.role, msg.category, msg.chat_id,
                                            msg.token_count, datetime.datetime.now())
        if logging:
            conversation_start_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                                       f"{self.config.CONVERSATION_START_LOG_MSG} "
                                                       f"{message.sender}"
                                                       f"{self.config.LOG_MSG_APPENDIX}",
                                                       'system', 'system', 'system', 'log', message.chat_id)
            self._log_message(conversation_start_log_msg)

    def _create_start_messages(self, message: OpenAIMessage) -> list[OpenAIMessage]:
        return [
            OpenAIMessage(self.config.SYSTEM_PROMPT, self.config.NAME, message.receiver,
                          'system', 'config', message.chat_id),
            OpenAIMessage(self.config.MY_NAME_IS + ' ' + message.sender.replace("_", " "),
                          message.sender, message.receiver, 'user', 'config', message.chat_id, token_count=7),
            OpenAIMessage(f'{self.config.I_WILL_CALL_YOU} {message.sender.split("_", 1)[0]}',
                          self.config.NAME, message.sender, 'assistant', 'config', message.chat_id, token_count=7),
        ]

    def _remove_conversation(self, chat_id: str) -> list:
        conversation = self.db.remove_conversation(chat_id)
        conversation_list = [OpenAIMessage(msg.message, msg.from_user, msg.to_user, msg.role, msg.category, msg.chat_id)
                             for msg in conversation]
        return conversation_list
