import datetime
import openai
from modules.database import Database
from modules.message import OpenAIMessage
from modules.config import Config
from modules.tools import clean_username
from modules.conversation import Conversation
from modules.ai import ChatPartner
import tiktoken


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

    def _talk_to_openai(self, message: OpenAIMessage) -> OpenAIMessage:
        message.token_count = self._get_token_count(message)
        if self._is_message_too_long(message):
            return self._handle_message_too_long(message)

        self._add_message_to_conversation(message)
        conversation: list[OpenAIMessage] = self._get_conversation(message.chat_id)

        response: dict = self._get_openai_response(conversation, self.config.MAX_TOKENS)
        response_message: OpenAIMessage = self._create_response_message(response, message)
        self._update_token_counts(message, response, response_message)
        self._add_message_to_conversation(response_message)
        return response_message

    def _get_token_count(self, message: OpenAIMessage) -> int:
        encoding = tiktoken.encoding_for_model(self.config.MODEL)
        num_token = len(encoding.encode(message.content))
        return num_token

    def _add_message_to_conversation(self, message: OpenAIMessage, logging: bool = True) -> None:
        if not self.db.check_conversation_exists(message.chat_id):
            self._start_conversation(message)
        self.db.add_message_to_messages(message.content, message.sender, message.receiver,
                                        message.role, message.category, message.chat_id,
                                        message.token_count, datetime.datetime.now())
        if logging:
            self._log_message(message)

    def _log_message(self, message: OpenAIMessage):
        self.db.add_message_to_system_log(message.content, message.sender, message.receiver,
                                          message.role, message.category, message.chat_id,
                                          message.token_count, datetime.datetime.now())

    def _get_conversation(self, chat_id: str) -> list[OpenAIMessage]:
        conversation = self.db.get_messages_from_db(chat_id)
        conversation_list = [OpenAIMessage(msg.message, msg.from_user, msg.to_user,
                                           msg.role, msg.category, msg.chat_id)
                             for msg in conversation]
        return conversation_list

    def _get_openai_response(self, messages: list[OpenAIMessage], max_tokens: int) -> dict:
        return openai.ChatCompletion.create(
            model=self.config.MODEL,
            messages=[msg.to_dict() for msg in messages],
            temperature=self.config.TEMPERATURE,
            max_tokens=max_tokens
        )

    def _create_response_message(self, response: dict, message: OpenAIMessage):
        reply = response["choices"][0]["message"]["content"]
        return OpenAIMessage(reply, self.config.NAME, message.sender, 'assistant', message.category, message.chat_id)

    def _update_token_counts(self, message: OpenAIMessage, response: dict,
                             response_message: OpenAIMessage) -> None:
        message_token_count: int = response["usage"]["prompt_tokens"]
        last_message = self.db.get_last_messages_from_db(message.chat_id, 1)[0]
        last_message.token_count = message_token_count
        response_message.token_count = response["usage"]["completion_tokens"]
        self.db.session.commit()

    def _is_message_too_long(self, message: OpenAIMessage) -> bool:
        last_message = self.db.get_last_messages_from_db(message.chat_id, 1)[0]
        return last_message.token_count > self.config.MAX_TOKENS

    def _handle_message_too_long(self, message: OpenAIMessage) -> OpenAIMessage:
        messages = self._remove_conversation(message.chat_id)
        if len(messages) < 7:
            self._start_conversation(message, logging=False)
            msg_too_long_error_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                                       f"{self.config.MESSAGE_TOO_LONG_LOG_MSG}"
                                                       f"{self.config.LOG_MSG_APPENDIX}",
                                                       'system', 'system', 'system', 'log', message.chat_id)
            msg_too_long_error_user_msg = OpenAIMessage(self.config.MESSAGE_TOO_LONG_USER_MSG.format(
                                                        max_tokens=self.config.MAX_TOKENS),
                                                        self.config.NAME, message.sender, 'assistant', 'user', message.chat_id)

            self._log_message(msg_too_long_error_log_msg)
            self._log_message(msg_too_long_error_user_msg)
            return msg_too_long_error_user_msg
        messages_to_append = messages[-3:]
        messages_to_summarize = messages[3:-3]
        summary_msg: OpenAIMessage = self._generate_summary(messages_to_summarize)
        self._start_conversation(message, logging=False)
        self._add_message_to_conversation(summary_msg, logging=False)
        self._log_message(OpenAIMessage(f"-> Conversation {message.chat_id} summarized...", 'system',
                                        'system', 'system', 'system_log'))
        self._log_message(summary_msg)
        for msg in messages_to_append:
            self._add_message_to_conversation(msg, logging=False)

    def _generate_summary(self, messages: list[OpenAIMessage]) -> OpenAIMessage or None:
        first_message = messages[0]
        conversation: str = ' '.join([msg.content for msg in messages])
        prompt = f"Summarize this conversation to natural language:\n{conversation}"
        request = OpenAIMessage(prompt, first_message.sender, first_message.receiver,
                                'user', first_message.chat_id)
        response: dict = self._get_openai_response([request], self.config.MAX_TOKENS_SUMMARY)
        response_message = self._create_response_message(response, first_message)
        response_message.token_count = response["usage"]["completion_tokens"]
        return response_message

    def _start_conversation(self, message: OpenAIMessage, logging: bool = True) -> None:
        msg_list = self._create_start_messages(message)
        for msg in msg_list:
            self.db.add_message_to_messages(msg.content, msg.sender, msg.receiver,
                                            msg.role, msg.chat_id, msg.token_count, datetime.datetime.now())
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
