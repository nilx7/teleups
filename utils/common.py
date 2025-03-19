from utils.nut import NUTClient

def get_ups_status_message(nut_client: NUTClient, title: str = "") -> tuple:
    """
    Get a UPS status message.

    Args:
        title (str): The title of the notification message.
    """
    title = title + "\n" + "UPS Status Information"
    msg = f"Battery Percentage: <b>{nut_client.get_battery_charge_percentage()}%</b>\n"
    msg += f"Status: <b>{nut_client.get_ups_status()}</b>\n"
    msg += f"Low Battery: <b>{'Yes' if nut_client.is_ups_battery_low(True) else 'No'}</b>\n"
    msg += f"Power: <b>{nut_client.get_current_power_draw()} watt</b>"
    return title, msg
