# Devices Folder
This folder contains Arduino sketch files for controlling various devices used in the LuciEntry Prototype. The sketches are designed to run on ESP8266 boards, such as NodeMCU or Wemos D1 Mini, which are Wi-Fi enabled microcontrollers.

## Architecture Overview
The device code is structured to perform specific tasks or control certain hardware components based on received commands from the server. Below is an explanation of the general architecture of the device code:

### Imports: 
The sketch begins with importing necessary libraries required for Wi-Fi connectivity, HTTP client, JSON parsing, NeoPixel LED control, and other functionalities.

### Setup Function: 
The setup() function initializes the device, configures the Wi-Fi connection, sets up GPIO pins, and initializes any necessary components.

### Loop Function: 
The loop() function is the main execution loop of the device. It continuously checks for commands from the server and executes corresponding actions.

### Wi-Fi Connection: 
The device connects to the Wi-Fi network specified by the SSID and password.

### Command Handling: 
The device periodically requests commands from the server. Upon receiving a command, it parses the JSON payload and executes the specified actions.

### HTTP Requests: 
The device sends HTTP requests to the server to fetch commands and post status updates.

### Command Execution: 
The device executes commands by controlling GPIO pins, interacting with sensors, or performing other hardware-related tasks.


# FAQ
- Q: If my device shows red light only, what does that mean?
  - A: Need to change the batteries before usage.
