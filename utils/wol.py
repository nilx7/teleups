from wakeonlan import send_magic_packet


class WakeOnLAN:

    def __init__(self, wol_mac_list: list):
        self.wol_mac_list = wol_mac_list

    def send_wol_magic_packet(self) -> bool:
        """
        Sends a Wake-on-LAN (WOL) magic packet to the MAC addresses stored in `self.wol_mac_list`.

        This function checks if `self.wol_mac_list` is populated. If it is empty or None,
        the function will return False without performing any action. Otherwise, it sends a magic packet
        using the `send_magic_packet` function and return True.
        """
        if not self.wol_mac_list:
            return False
        send_magic_packet(*self.wol_mac_list)
        return True
