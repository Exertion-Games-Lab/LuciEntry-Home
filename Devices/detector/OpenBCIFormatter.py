"""
Class for formatting LR data into viewable openBCI format for GUI.
Please note: This also creates and saves a file of the openbci data as well

Author: Neth Botheju 2024
"""
from datetime import date


class OpenBCIFormatter:
    def __init__(self, file_name, left_data, right_data):
        """
        Initializes OpenBCIFormatter with left and right data.

        Parameters:
            file_name (string): Name of file to write output to.
            left_data (list or array): The left side data to be formatted.
            right_data (list or array): The right side data to be formatted.
        """
        self.file_name = file_name
        self.left_data = left_data
        self.right_data = right_data

    def format_message(self):
        """
        Formats the left and right data into an OpenBCI-compatible message format.

        Returns:
            str: The formatted message as a string so you can save it in a file.
        """
        header = "<OpenBCI Start>"
        footer = "<OpenBCI End>"

        # Format left and right data as comma-separated values
        left_data_str = ",".join(map(str, self.left_data))
        right_data_str = ",".join(map(str, self.right_data))

        # Create the formatted message
        message = f"{header} LEFT:{left_data_str} RIGHT:{right_data_str} {footer}"

        self.file_name = "OpenBCI_RAW_" + self.file_name
        f = open(self.file_name, "a")
        f.write(message)
        f.close()

        return message