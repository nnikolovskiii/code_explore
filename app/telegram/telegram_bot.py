# app/telegram/telegram_bot.py
import logging
import os
from typing import Optional

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)
from telegram.constants import ParseMode
from dotenv import load_dotenv

from app.chat.service import ChatService
from app.llms.models import ChatLLM

load_dotenv()

class TelegramBot:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
        self.token = os.getenv("TELEGRAM_TOKEN")
        # Create the Application instance first
        self.application = ApplicationBuilder().token(self.token).build()
        self.bot = self.application.bot
        self.model: Optional[ChatLLM] = None
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def initialize_model(self):
        """Async initialization of model"""
        self.model = await self.chat_service.get_model("gpt-4o", ChatLLM)

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Hello! I'm your AI assistant. How can I help you today?")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.model:
            await update.message.reply_text("Bot is initializing, please wait...")
            return

        chat_id = update.message.chat_id
        user_message = update.message.text
        logging.info(f"Received message from {chat_id}: {user_message}")

        # Get response from AI model
        try:
            response = await self.model.generate(user_message)
            await self.send_message(response, chat_id)
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            await self.send_message("Sorry, I encountered an error processing your request.", chat_id)

    async def send_message(self, message: str, chat_id: int):
        try:
            # Escape special MarkdownV2 characters
            escaped_message = self._escape_markdown(message)

            await self.bot.send_message(
                chat_id=chat_id,
                text=escaped_message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_notification=False,
                protect_content=True,
            )
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    def _escape_markdown(self, text: str) -> str:
        """Escape special MarkdownV2 characters"""
        escape_chars = '_*[]~`>#+-=|{}.!'
        return ''.join(['\\' + char if char in escape_chars else char for char in text])

    async def start(self):
        """Start the bot with polling"""
        await self.initialize_model()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

    async def stop(self):
        """Stop the bot gracefully"""
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
