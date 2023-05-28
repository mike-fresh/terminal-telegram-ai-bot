from telegram import ForceReply, Update, MessageEntity
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from modules.chatbot_base import ChatBot
from modules.message import OpenAIMessage
from modules.tools import clean_username
from modules.picture import Picture
from modules.conversation import Conversation

class TelegramBot(ChatBot):
    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            user = update.effective_user
            username = clean_username(user.full_name)
            print(f"User {username} executed /start command.")
            # TODO: remove this print statement and log to database instead
            await update.message.reply_html(
                f"{self.config.TELEGRAM_START_MESSAGE.format(user=user.mention_html(), name=self.config.NAME, model=self.config.MODEL)}",
                reply_markup=ForceReply(selective=True)
            )

        async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            user = update.effective_user
            username = clean_username(user.full_name)
            conversation = Conversation(str(update.effective_chat.id), username)
            conversation.clear_messages()
            print(f"User {username} executed /reset command.")
            await update.message.reply_text(f"{self.config.CONSOLE_RESET_MSG}")
            # TODO: remove this print statement and log to database instead

        async def pic_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            user = update.effective_user
            user_input = context.args[0]
            username = clean_username(user.full_name)
            picture = Picture(user_input)
            # TODO: remove this print statement and log to database instead
            # TODO: save the picture to the database
            print(f"User {username} executed /pic command.")
            with open(f"generated_image-{picture.timestamp_string}.png", "rb") as f:
                await update.message.reply_photo(photo=f, caption=self.config.TELEGRAM_IMAGE_CAPTION)

        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            user = update.effective_user
            username = clean_username(user.full_name)
            print(f"User {username} executed /help command.")
            # TODO: remove this print statement and log to database instead
            await update.message.reply_text(f"{self.config.TELEGRAM_HELP_MESSAGE}")

        async def answer_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            # TODO: remove the print statements and log to database instead
            username = clean_username(update.effective_user.full_name)
            chat_id = update.message.chat_id
            # answer to a reply-message from a user in a group
            if update.message.chat.type == 'group':
                if update.effective_message.reply_to_message and \
                        update.effective_message.reply_to_message.from_user.id == context.bot.id:
                    print(f"User {username} replied to {self.config.NAME} in chat id {chat_id}.")
                    await update.message.reply_text(self.send_message(update))
                # answer to a mention in a group
                if update.effective_message.entities:
                    for entity in update.effective_message.entities:
                        if entity.type == MessageEntity.MENTION:
                            print(f"User {username} mentioned {self.config.NAME} in chat id {chat_id}.")
                            await update.message.reply_text(self.send_message(update))
            # if not in a group, just answer to the message
            else:
                print(f"User {username} sent message to {self.config.NAME} in chat id {chat_id}.")
                await update.message.reply_text(self.send_message(update))
        try:
            application: Application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("reset", reset_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("pic", pic_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_to_message))
            print(self.config.TELEGRAM_STARTED_MESSAGE.format(name=self.config.NAME))
            application.run_polling()
            print(self.config.TELEGRAM_STOPPED_MESSAGE.format(name=self.config.NAME))
        except KeyboardInterrupt:
            print(self.config.TELEGRAM_STOPPED_MESSAGE.format(name=self.config.NAME))

    def send_message(self, update: Update) -> str or None:
        user = update.effective_user
        username = clean_username(user.full_name)
        msg_obj: OpenAIMessage = OpenAIMessage(update.message.text,
                                               username, self.config.NAME,
                                               'user', 'user', str(update.effective_chat.id))
        answer_from_openai: OpenAIMessage = self.process_message(msg_obj)
        return answer_from_openai.content
