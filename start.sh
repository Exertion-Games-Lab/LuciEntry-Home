#!/bin/bash

# Function to find folder path
find_folder_path() {
    # Specify the starting directory for finding LDI-System-main
    STARTING_PATH="/home/"

    # Find the path to LDI-System-main
    SYSTEM_PATH=$(find "$STARTING_PATH" -type d -name "LuciEntry-Home" 2>/dev/null | head -n 1)

    # If LDI-System-main is found, find the API folder within it
    if [ -n "$SYSTEM_PATH" ]; then
        SERVER_FOLDER=$(find "$SYSTEM_PATH" -type d -name "Server" 2>/dev/null | head -n 1)
        #COMMAND_SCRIPTS_FOLDER=$(find "$SYSTEM_PATH" -type d -name "Command-Scripts" 2>/dev/null | head -n 1)
        SPEAKERS_DEVICES_FOLDER=$(find / -type d -name "Device_3-Speakers" 2>/dev/null | head -n 1)
        DETECTOR_FOLDER=$(find "$SYSTEM_PATH" -type d -name "Detector" 2>/dev/null | head -n 1)
    else
        echo "LuciEntry-Home folder not found."
        exit 1
    fi
}

# Function to start the server
start_server() {
    lxterminal --title="Server" --working-directory="$SERVER_FOLDER" -e "bash -c 'npm start && read -p \"Press ENTER to exit\"'"
}

# Function to run Python script in another terminal
run_python_script() {
    sleep 15
    lxterminal --title="Speaker" --working-directory="$SPEAKERS_DEVICES_FOLDER" -e "bash -c 'python Device_3-Speakers.py && read -p \"Press ENTER to exit\"'"
    #lxterminal --title="Command Sender" --working-directory="$COMMAND_SCRIPTS_FOLDER" -e "bash -c 'python CommandSender.py && read -p \"Press ENTER to exit\"'"
    lxterminal --title="Detector" --working-directory="$DETECTOR_FOLDER" -e "bash -c 'python Detector.py && read -p \"Press ENTER to exit\"'"
}

# Add more functions if needed

# Main script starts here

# Find folder paths
find_folder_path

# Start the server
start_server

# Run Python script
run_python_script

# Add more commands or functions if needed

read -p "Press Enter to exit"
