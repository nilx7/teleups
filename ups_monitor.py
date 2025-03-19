import time
import logging
import threading
import schedule
from typing import Optional
from utils.wol import WakeOnLAN
from utils.nut import NUTClient
from utils.telegram_notifier import TelegramNotifier
from utils import common
from logger_setup import handle_logging


class UPSMonitor:
    """
    A class to monitor UPS status and send notifications for power outages and restorations.
    """

    def __init__(
        self,
        nut_client: NUTClient,
        telegram_notifier: TelegramNotifier,
        wol_mac_list=None,
        auto_wake_interval: int = 0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initializes the UPSMonitor.

        Args:
            nut_client: An instance of a NUT client to interact with the UPS.
            telegram_notifier: An instance of TelegramNotifier to send notifications.
            wol_make_list: A list of MAC addresses for devices to be awakened using Wake-on-LAN (WOL).
            auto_wake_interval (int): The time interval (in minutes) for periodically waking devices using Wake-on-LAN (WOL).
            logger (Optional[logging.Logger]): A logger instance for logging messages. Defaults to None.
        """
        self.nut_client = nut_client
        self.last_ups_on_battery_status = False
        self.last_ups_low_battery_status = False
        self.telegram_notifier = telegram_notifier
        self.wol_mac_list = wol_mac_list
        self.wol = WakeOnLAN(wol_mac_list) if wol_mac_list else None
        self.auto_wake_interval = auto_wake_interval
        self.logger = logger or logging.getLogger(__name__)
        handle_logging(logging.INFO, "Monitor started", self.logger)

    def send_ups_status_notification(self, title: str = "") -> None:
        """
        Sends a UPS status notification via Telegram.

        Args:
            title (str): The title of the notification message.
        """
        title, msg = common.get_ups_status_message(self.nut_client, title)
        self.telegram_notifier.send_notification(title, msg)
        handle_logging(logging.INFO, "UPS status notification sent", self.logger)

    def handle_power_outage(self) -> None:
        """
        Handles the UPS power outage scenario.
        """
        handle_logging(logging.INFO, "UPS status changed (Power Outage)", self.logger)
        self.send_ups_status_notification(title="Power outage!")

        current_battery_perc = self.nut_client.get_battery_charge_percentage()
        current_ups_low_battery_status = self.nut_client.is_ups_battery_low()

        if current_ups_low_battery_status and not self.last_ups_low_battery_status:
            handle_logging(
                logging.INFO, f"Low battery status {current_battery_perc}%", self.logger
            )
            self.send_ups_status_notification(title="Low battery!")

        self.last_ups_low_battery_status = current_ups_low_battery_status

    def handle_power_restoration(self) -> None:
        """
        Handles the UPS power restoration scenario.
        """
        handle_logging(
            logging.INFO, "UPS status changed (Power Restoration)", self.logger
        )
        self.send_ups_status_notification(title="Power restoration!")

        self.send_wol_magic_packet()

    def send_wol_magic_packet(self) -> None:
        """
        Sends a Wake-on-LAN (WOL) magic packet if certain conditions are met.

        This function ensures that the WOL packet is only sent when:
        - `self.wol` is set (not None or False).
        - The UPS is not currently running on battery power.
        - The battery charge level is above the low battery threshold.
        """
        if (
            not self.wol
            or self.nut_client.is_ups_on_battery()
            or (
                self.nut_client.get_battery_charge_percentage()
                <= self.nut_client.get_battery_charge_low_percentage()
            )
        ):
            return

        self.wol.send_wol_magic_packet()
        handle_logging(
            logging.INFO,
            f"WOL magic packet successfully sent to: {self.wol_mac_list}",
            self.logger,
        )

    def check_ups_status(self) -> None:
        """
        Monitors the UPS status and handles power outage/restoration events.
        """
        current_ups_on_battery_status = self.nut_client.is_ups_on_battery()

        # Power outage
        if not self.last_ups_on_battery_status and current_ups_on_battery_status:
            self.handle_power_outage()
        # Power restoration
        elif self.last_ups_on_battery_status and not current_ups_on_battery_status:
            self.handle_power_restoration()

        self.last_ups_on_battery_status = current_ups_on_battery_status

    def monitor_ups(self) -> None:
        """
        Schedules a routine check
        """
        try:
            schedule.every(10).seconds.do(self.check_ups_status)
            if self.auto_wake_interval > 0:
                schedule.every(self.auto_wake_interval).minutes.do(
                    self.send_wol_magic_packet
                )

            threading.Thread(
                target=self.telegram_notifier.create_bot_application,
                args=(self.nut_client,),
                daemon=True
            ).start()            

            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            handle_logging(logging.INFO, "Script terminated by user", self.logger)
