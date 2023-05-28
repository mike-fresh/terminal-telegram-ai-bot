import argparse
import openai
import telegram
from modules.telegrambot import TelegramBot
from modules.consolebot import ConsoleBot
from modules.config import Config

config = Config()
openai.api_key = config.OPENAI_API_KEY


def main(arguments):
    if arguments.telegram:
        bot: TelegramBot = TelegramBot()
        bot.run()
    else:
        bot: ConsoleBot = ConsoleBot()
        bot.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f'{config.NAME} {config.ARG_PARSER_INFO}')
    parser.add_argument('--telegram', action='store_true', help='start bot as a Telegram bot')
    args = parser.parse_args()
    for i in range(int(config.CONNECTION_MAX_TRIES) + 1):
        try:
            main(args)
        except openai.error.APIConnectionError as e:
            print(config.CONNECTION_ERROR_MESSAGE + ":", e, sep='\n')
        except telegram.error.NetworkError as e:
            print(config.CONNECTION_ERROR_MESSAGE + ":", e, sep='\n')
