"""
Class for formatting LR data into viewable openBCI format for GUI.
Please note: This also creates and saves a file of the openbci data as well

Author: Neth Botheju 2024
"""
from datetime import date


class OpenBCIFormatter:
    def __init__(self, file_name):
        """
        Initializes OpenBCIFormatter with left and right data.

        Parameters:
            file_name (string): Name of file to write output to.
            left_data (list or array): The left side data to be formatted.
            right_data (list or array): The right side data to be formatted.
        """
        self.file_name = "OpenBCI_RAW_" + file_name
        header = ("%OpenBCI Raw EXG Data\n%Number of channels = 2\n%Sample Rate = 250 Hz\n%Board = OpenBCI_GUI$BoardCytonSerial\n"
                  "")

        f = open(self.file_name, "a")
        f.write(header)
        f.close()

    def format_message(self, eog_left_data, eog_right_data):
        """
        Formats the left and right data into an OpenBCI-compatible message format.

        Returns:
            str: The formatted message as a string so you can save it in a file.
        """

        # Format left and right data as comma-separated values
        left_data_str = ",".join(map(str, eog_left_data))
        right_data_str = ",".join(map(str, eog_right_data))

        # Create the formatted message
        message = f"LEFT:{left_data_str} RIGHT:{right_data_str}"

        f = open(self.file_name, "a")
        f.write(message)
        f.close()

        return message