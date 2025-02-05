import logging
import os

from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

class TelegramBot:
    bot: Bot

    def __init__(self):
        load_dotenv()
        bot_token = os.getenv("TELEGRAM_TOKEN")
        self.bot = Bot(token=bot_token)


    async def send_message(self, message: str, chat_id: int):
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_notification=False,
                protect_content=True,
            )
        except Exception as e:
            logging.error(e)
