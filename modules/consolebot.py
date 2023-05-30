import sys
import readline
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from modules.chatbot_base import ChatBot
from modules.message import OpenAIMessage


class ConsoleBot(ChatBot):
    def __init__(self) -> None:
        super().__init__()
        self.commands = {
            "/start": self.reset,
            "/restart": self.reset,
            "/reset": self.reset,
            "/quit": self.stop,
            "/exit": self.stop,
            "/stop": self.stop,
            "/bye": self.stop,
        }
        self.SEPARATOR_LINE: str = u"\033[32m" + "*" * 80 + u"\033[0m"
        self.conversation_reset_log_msg = OpenAIMessage(f"{self.config.LOG_MSG_PREFIX} "
                                                        f"{self.config.CONVERSATION_RESET_LOG_MSG} "
                                                        f"{self.LOCAL_USERNAME}"
                                                        f"{self.config.LOG_MSG_APPENDIX}",
                                                        'system', 'system', 'system', 'log', 'system_log')

    def run(self) -> None:
        try:
            print(self.SEPARATOR_LINE)
            while True:
                user_input: str = self._get_user_input()
                print(u"\033[0m", end="")
                if user_input == "":
                    continue
                answer: str = self._send_message(user_input)
                print(u"\033[0m" + answer, end="")
        except KeyboardInterrupt:
            self.stop()

    def reset(self) -> str:
        self._remove_conversation('system_console')
        self._start_conversation(OpenAIMessage('', self.LOCAL_USERNAME, self.config.NAME,
                                               'system', 'log', 'system_console'),
                                 logging=False)
        self._log_message(self.conversation_reset_log_msg)
        return f'{self.config.CONSOLE_RESET_MSG}'

    def stop(self) -> None:
        self._log_message(self.stop_log_msg)
        print(u"\033[0m" + self.config.BYE_MESSAGE)
        sys.exit(0)

    def _get_user_input(self) -> str:
        contents: list = []
        readline.parse_and_bind("")
        while True:
            try:
                sys.stdout.write(u"\033[32m")
                line: str = input()
                sys.stdout.write(u"\033[0m")
                sys.stdout.write("\n") if line == "" else None
            except EOFError:
                print(self.SEPARATOR_LINE)
                break
            contents.append(line)
        return "\n".join(contents)

    def _send_message(self, message: str) -> str or None:
        if message.strip() == '':
            return
        command = self.commands.get(message)
        if command:
            return command() + "\n" + self.SEPARATOR_LINE + "\n"
        msg_obj: OpenAIMessage = OpenAIMessage(message, self.LOCAL_USERNAME, self.config.NAME,
                                               'user', 'user', 'system_console')
        answer_from_openai: OpenAIMessage = self.process_message(msg_obj)
        highlighted_reply: str = self.format_codeblock(answer_from_openai.content)
        return highlighted_reply + self.SEPARATOR_LINE + "\n"

    @staticmethod
    def format_codeblock(text: str) -> str:
        highlighted_text: str = ""
        in_code_block: bool = False
        for line in text.split("\n"):
            if line.startswith("```"):
                in_code_block = not in_code_block
                highlighted_text += highlight(line, PythonLexer(), TerminalFormatter()) + "\n"
            elif in_code_block:
                highlighted_text += highlight(line, PythonLexer(), TerminalFormatter()) + "\n"
            else:
                highlighted_text += line + "\n"
        highlighted_text = "\n".join(line for line in highlighted_text.split("\n") if line.strip())
        return highlighted_text + "\n"
