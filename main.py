#!/usr/bin/python3

from utils.nut import NUTClient
from logger_setup import setup_logger
from utils.telegram_notifier import TelegramNotifier
from ups_monitor import UPSMonitor
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration Constants
TELEGRAM_TOKEN_ID = os.getenv('TELEGRAM_TOKEN_ID')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
NUT_CLIENT_NAME = os.getenv('NUT_CLIENT_NAME')
NUT_CLIENT_HOST = os.getenv('NUT_CLIENT_HOST')
NUT_CLIENT_USER = os.getenv('NUT_CLIENT_USER')
NUT_CLIENT_PASSWORD = os.getenv('NUT_CLIENT_PASSWORD')
WOL_MAC_LIST = [item.strip() for item in os.getenv('WOL_MAC_LIST', '').split(",") if item.strip()]

def main():
    logger = setup_logger()
    telegram_notifier = TelegramNotifier(token_id=TELEGRAM_TOKEN_ID, chat_id=TELEGRAM_CHAT_ID, logger=logger)
    nut_client = NUTClient(NUT_CLIENT_NAME, NUT_CLIENT_HOST, NUT_CLIENT_USER, NUT_CLIENT_PASSWORD)
    ups_monitor = UPSMonitor(nut_client, telegram_notifier, WOL_MAC_LIST, logger)
    ups_monitor.monitor_ups()

if __name__ == "__main__":
    main()
