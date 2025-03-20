import requests
import logging
import asyncio
from typing import Optional
from utils import common
from logger_setup import handle_logging
from telegram import Chat, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)


class TelegramNotifier:
    """
    A class to send notifications to a Telegram chat.
    """

    def __init__(
        self, token_id: str, chat_id: str, logger: Optional[logging.Logger] = None
    ):
        """
        Initializes the TelegramNotifier.

        Args:
            token_id (str): The token ID of the Telegram bot.
            chat_id (str): The chat ID to send messages to.
            logger (Optional[logging.Logger]): A logger instance for logging messages. Defaults to None.
        """
        self.token_id = token_id
        self.chat_id = chat_id
        self.logger = logger or logging.getLogger(__name__)

    def get_full_html_message(self, msg_title: str, msg: str) -> str:
        post_msg = "Your faithful employee,\nTeleUPS"
        full_msg = f"<b>{msg_title}</b>\n\n{msg}\n\n<b>{post_msg}</b>"
        return full_msg

    def send_notification(self, msg_title: str, msg: str) -> None:
        """
        Sends a notification to the specified Telegram chat.

        Args:
            msg_title (str): The title of the message.
            msg (str): The body of the message.
        """
        full_msg = self.get_full_html_message(msg_title, msg)

        payload = {"chat_id": self.chat_id, "text": full_msg, "parse_mode": "HTML"}
        url = f"https://api.telegram.org/bot{self.token_id}/sendMessage"
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            handle_logging(
                logging.INFO,
                "Telegram notification has been sent successfully",
                self.logger,
            )
        except requests.exceptions.RequestException as e:
            handle_logging(
                logging.ERROR, f"Failed to send Telegram notification: {e}", self.logger
            )

    async def reply_ups_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat = update.effective_chat

        if (
            chat.type != Chat.CHANNEL
            or str(chat.id) != self.chat_id
            or update.effective_message.text != "/ups"
        ):
            return

        msg_title, msg = common.get_ups_status_message(self.nut_client)
        full_msg = self.get_full_html_message(msg_title, msg)

        await update.effective_message.reply_text(full_msg, parse_mode=ParseMode.HTML)

    async def botloop_routine(self):
        application = Application.builder().token(self.token_id).build()
        application.add_handler(
            MessageHandler(filters.ChatType.CHANNEL, self.reply_ups_status)
        )

        await application.initialize()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        await application.start()

        while True:
            await asyncio.sleep(1)

    async def botloop_start(self):
        bot_routine = asyncio.create_task(self.botloop_routine())
        await bot_routine

    def create_bot_application(self, nut_client):
        self.nut_client = nut_client
        asyncio.run(self.botloop_start())
