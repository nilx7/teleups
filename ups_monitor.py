import time
import logging
from typing import Optional
from wakeonlan import send_magic_packet

class UPSMonitor:
    """
    A class to monitor UPS status and send notifications for power outages and restorations.
    """

    def __init__(self, nut_client, telegram_notifier, wol_mac_list = None, logger: Optional[logging.Logger] = None):
        """
        Initializes the UPSMonitor.

        Args:
            nut_client: An instance of a NUT client to interact with the UPS.
            telegram_notifier: An instance of TelegramNotifier to send notifications.
            logger (Optional[logging.Logger]): A logger instance for logging messages. Defaults to None.
        """
        self.nut_client = nut_client
        self.last_ups_on_battery_status = False
        self.last_ups_low_battery_status = False
        self.telegram_notifier = telegram_notifier
        self.wol_mac_list = wol_mac_list
        self.logger = logger or logging.getLogger(__name__)
        self.handle_logging(logging.INFO, "Monitor started")

    def handle_logging(self, level: int, message: str) -> None:
        """
        Handles logging or printing messages based on the availability of a logger.

        Args:
            level (int): The log level for the message.
            message (str): The message to log or print.
        """
        if self.logger:
            self.logger.log(level, message)
        else:
            print(message)

    def send_ups_status_notification(self, title: str = "") -> None:
        """
        Sends a UPS status notification via Telegram.

        Args:
            title (str): The title of the notification message.
        """
        title = title + "\n" + "UPS Status Information"
        msg = f"Battery Percentage: <b>{self.nut_client.get_battery_charge_percentage()}%</b>\n"
        msg += f"Status: <b>{self.nut_client.get_ups_status()}</b>\n"
        msg += f"Low Battery: <b>{'Yes' if self.nut_client.is_ups_battery_low(True) else 'No'}</b>\n"
        msg += f"Power: <b>{self.nut_client.get_current_power_draw()} watt</b>"
        self.telegram_notifier.send_notification(title, msg)
        self.handle_logging(logging.INFO, "UPS status notification sent")

    def handle_power_outage(self) -> None:
        """
        Handles the UPS power outage scenario.
        """
        self.handle_logging(logging.INFO, "UPS status changed (Power Outage)")
        self.send_ups_status_notification(title="Power outage!")

        current_battery_perc = self.nut_client.get_battery_charge_percentage()
        current_ups_low_battery_status = self.nut_client.is_ups_battery_low()

        if current_ups_low_battery_status and not self.last_ups_low_battery_status:
            self.handle_logging(logging.INFO, f"Low battery status {current_battery_perc}%")
            self.send_ups_status_notification(title="Low battery!")

        self.last_ups_low_battery_status = current_ups_low_battery_status

    def handle_power_restoration(self) -> None:
        """
        Handles the UPS power restoration scenario.
        """
        self.handle_logging(logging.INFO, "UPS status changed (Power Restoration)")
        self.send_ups_status_notification(title="Power restoration!")
        self.send_wol_magic_packet()

    def send_wol_magic_packet(self) -> None:
        """
        Sends a Wake-on-LAN (WOL) magic packet to the MAC addresses stored in `self.wol_mac_list`.

        This function checks if `self.wol_mac_list` is populated. If it is empty or None, 
        the function exits without performing any action. Otherwise, it sends a magic packet 
        using the `send_magic_packet` function.
        """
        if not self.wol_mac_list:
            return
        send_magic_packet(*self.wol_mac_list)
        self.handle_logging(logging.INFO, f"WOL magic packet sent to: {self.wol_mac_list}")

    def monitor_ups(self) -> None:
        """
        Monitors the UPS status in a loop and handles power outage/restoration events.
        """
        try:
            while True:
                current_ups_on_battery_status = self.nut_client.is_ups_on_battery()

                # Power outage
                if not self.last_ups_on_battery_status and current_ups_on_battery_status:
                    self.handle_power_outage()
                # Power restoration
                elif self.last_ups_on_battery_status and not current_ups_on_battery_status:
                    self.handle_power_restoration()

                self.last_ups_on_battery_status = current_ups_on_battery_status
                time.sleep(30)  # Wait for 30 seconds before checking again

        except KeyboardInterrupt:
            self.handle_logging(logging.INFO, "Script terminated by user.")
