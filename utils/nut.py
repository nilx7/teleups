from PyNUTClient.PyNUT import PyNUTClient


class NUTClient:
    def __init__(self, ups_name, ups_host, ups_login_user, ups_login_pass):
        """
        Initializes a NUTClient instance.

        Args:
        - ups_name (str): Name of the UPS device.
        - ups_host (str): Hostname or IP address of the NUT server.
        - ups_login_user (str): Username for logging into the NUT server.
        - ups_login_pass (str): Password for logging into the NUT server.
        """
        self.ups_name = ups_name
        self.client = PyNUTClient(host=ups_host, login=ups_login_user, password=ups_login_pass)

    @staticmethod
    def __decode_byte_dict(byte_dict: dict) -> dict:
        """
        Decodes keys and values of a byte-encoded dictionary from UTF-8.

        Args:
        - byte_dict (dict): Dictionary with byte-encoded keys and values.

        Returns:
        - dict: Dictionary with decoded keys and values as strings.
        """
        return {key.decode('utf-8'): value.decode('utf-8') for key, value in byte_dict.items()}

    def __handle_operation(self, operation, *args, **kwargs):
        """
        Handles common error handling for operations with the NUT client.

        Args:
        - operation (callable): Callable representing a method of PyNUTClient.
        - args: Positional arguments to pass to the operation.
        - kwargs: Keyword arguments to pass to the operation.

        Returns:
        - Any: Result of the operation, or None if an error occurs.
        """
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    def is_ups_available(self) -> bool:
        """
        Checks if the UPS device is available.

        Returns:
        - bool: True if the UPS is available, False otherwise.
        """
        return self.__handle_operation(self.client.CheckUPSAvailable, ups=self.ups_name)

    def get_ups_read_write_vars(self) -> dict:
        """
        Retrieves read-write variables of the UPS device.

        Returns:
        - dict: Dictionary containing read-write variables of the UPS.
        """
        response = self.__handle_operation(self.client.GetRWVars, ups=self.ups_name)
        return self.__decode_byte_dict(response) if response else {}

    def get_ups_vars(self) -> dict:
        """
        Retrieves variables of the UPS device.

        Returns:
        - dict: Dictionary containing variables of the UPS.
        """
        response = self.__handle_operation(self.client.GetUPSVars, ups=self.ups_name)
        return self.__decode_byte_dict(response) if response else {}

    def get_ups_list(self) -> dict:
        """
        Retrieves the list of UPS devices connected to the NUT server.

        Returns:
        - dict: Dictionary containing the list of UPS devices.
        """
        response = self.__handle_operation(self.client.GetUPSList)
        return self.__decode_byte_dict(response) if response else {}

    def get_current_power_draw(self) -> int:
        """
        Retrieves the current power being drawn from the UPS in watts.

        This method accesses the UPS variables using the `get_ups_vars` method and retrieves the 
        value of the 'ups.realpower' key, which represents the current power draw in watts. If the 
        'ups.realpower' key is not present in the dictionary, it defaults to '0'. The value is then 
        converted to an integer and returned.

        Returns:
            int: The current power draw from the UPS in watts. Returns 0 if the value is not available.
        """
        ups_vars = self.get_ups_vars()
        return int(ups_vars.get('ups.realpower', '0'))

    def get_battery_charge_percentage(self) -> int:
        """
        Retrieves the current battery charge percentage of the UPS device.

        Returns:
        - int: Current battery charge percentage.
        """
        ups_vars = self.get_ups_vars()
        return int(ups_vars.get('battery.charge', 0)) if ups_vars else 0

    def get_battery_charge_low_percentage(self) -> int:
        """
        Retrieves the low battery charge percentage threshold from the UPS's read/write variables.

        This function accesses the UPS's read/write variables to obtain the 'battery.charge.low' value,
        which indicates the battery charge percentage at which the UPS considers the battery to be low.
        If the value is not found or if an error occurs while accessing the variables, it returns 0.

        Returns:
            int: The battery charge low percentage threshold. Returns 0 if the value is not available or
                if an error occurs.
        """
        ups_rwvars = self.get_ups_read_write_vars()
        return int(ups_rwvars.get('battery.charge.low', 0)) if ups_rwvars else 0

    def is_ups_on_battery(self) -> bool:
        """
        Checks if the UPS device is currently running on battery power.

        Returns:
        - bool: True if the UPS is on battery power ('OB' status), False otherwise.
        """
        ups_vars = self.get_ups_vars()
        return 'OB' in ups_vars.get('ups.status') if ups_vars else False

    def is_ups_battery_low(self, ignore_ob: bool = False) -> bool:
        """
        Checks if the UPS battery charge is below the configured low battery threshold.

        This method determines whether the UPS battery charge is considered low by comparing the current
        battery charge percentage with the low battery threshold. By default, it only checks the battery
        status if the UPS is currently running on battery power (online battery status 'OB'). This behavior
        can be overridden with the `ignore_ob` parameter.

        Args:
            ignore_ob (bool): If True, the method will ignore whether the UPS is on battery power and will
                            only compare the battery charge percentage with the low battery threshold.
                            Defaults to False.

        Returns:
            bool: True if the UPS battery charge is below or equal to the low battery threshold, False otherwise.
        """
        if not self.is_ups_on_battery() and not ignore_ob:
            return False
        return self.get_battery_charge_percentage() <= self.get_battery_charge_low_percentage()

    def get_ups_status(self) -> str:
        """
        Retrieves the descriptive status of the UPS device.

        Returns:
        - str: Description of the current status of the UPS device.
                Possible status descriptions:
                - 'OL': On Line (UPS is on mains power)
                - 'OB': On Battery (UPS is on battery power)
                - 'LB': Low Battery (Battery is low)
                - 'CHRG': Charging (Battery is charging)
                - 'DISCHRG': Discharging (Battery is discharging)
                - 'BYPS': Bypass (UPS is bypassed)
                - 'OFF': Offline (UPS is off)
                - 'TRIM': SmartTrim (UPS is trimming the voltage)
                - 'BOOST': SmartBoost (UPS is boosting the voltage)
        """
        status_map = {
            'OL': 'On Line',
            'OB': 'On Battery',
            'LB': 'Low Battery',
            'CHRG': 'Charging',
            'DISCHRG': 'Discharging',
            'BYPS': 'Bypass',
            'OFF': 'Offline',
            'TRIM': 'SmartTrim',
            'BOOST': 'SmartBoost',
        }

        ups_vars = self.get_ups_vars()
        if ups_vars:
            status_codes = ups_vars.get('ups.status', '').split()
            status_descriptions = [status_map.get(code, 'Unknown status') for code in status_codes]

            # Filter out 'Unknown status' if at least one known status is detected
            known_statuses = [desc for desc in status_descriptions if desc != 'Unknown status']
            if known_statuses:
                return ', '.join(known_statuses)
            else:
                return 'Unknown status'
        else:
            return 'Unknown status'
