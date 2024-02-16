# Table of Contents

1. [System Structure](#system-structure)

2. [System Architecture](#system-architecture)

3. [New Pi Setup Procedure](#new-pi-setup-procedure)

4. [User Guide](#user-guide)

This README markdown file contains the system structure as well as the first time setup and user guides for the server that controls the LuciEntry prototype, developed by Exertion Games Lab for Lucid Dreaming research. In this document, the system file structure is outlined, and the process of setting up a new raspberry Pi with the server codes.
# System Structure
The Server file consist of a main folder named LuciEntry.

## Folder: LuciEntry
This is the main folder which contains the sub-folders "Server", "Command-Scripts" and "Devices". It also contains the "start.sh" shell file, "configure_wifi.py" python program, the "wifi_info.json" JSON file, and this README.md markdown file.

### Shell File: start.sh
This shell script is designed to automate the setup and execution of a server and a Python script in separate terminal windows on a Raspberry Pi. Below are the key functionalities of the script:

#### Find Folder Path Function:
  - Searches for the LuciEntry folder in the /home/ directory.
  - If found, locates the Server folder within LuciEntry.
  - Searches for the Device_3-Speakers folder in the root directory.

#### Start Server Function:
  - Opens a new terminal window using lxterminal.
  - Sets the working directory to the Server folder.
  - Executes npm start command to start the server.
  - Waits for user input (Press ENTER to exit).

#### Run Python Script Function:
  - Waits for a specified duration (15 seconds) to ensure the server is started.
  - Opens a new terminal window using lxterminal.
  - Sets the working directory to the Device_3-Speakers folder.
  - Executes python Device_3-Speakers.py command to run the Python script.
  - Waits for user input (Press ENTER to exit).

#### Main Script Execution:
  - Calls the find_folder_path function to locate required folders.
  - Starts the server using start_server function.
  - Runs the Python script using run_python_script function.
  - Prompts the user to press ENTER to exit the script.

This script enables the seamless setup and execution of a server and a Python script for Lucid Dreaming Prototype on a Raspberry Pi.

### Python File: confgure_wifi.py
This Python script is designed to update Wi-Fi configuration details in various files used for the Lucid Dreaming Prototype project. Below are the key functionalities of the script:

#### Retrieve Wi-Fi Information Functions:
Utilizes subprocesses to obtain the current Wi-Fi SSID and IP address of the Raspberry Pi.

#### Folder and File Search Functions:
Searches for specific folders and files within the /home/ directory, particularly the LuciEntry folder and its subfolders.

#### Update Script Functions:
Updates Python and Arduino script files with the latest Wi-Fi configuration details stored in a JSON file (wifi_info.json).

#### Main Function:
Displays a welcome message with the project logo.
Checks if the current Wi-Fi SSID matches the stored SSID.
Prompts the user to change Wi-Fi details if needed, updating the wifi_info.json file accordingly.
Updates Wi-Fi configuration in Python and Arduino script files.
Prints status messages indicating whether changes were made or if the server is ready to run.

#### Execution:
Invokes the main function when the script is run.

This Python script streamlines the process of updating Wi-Fi configuration details across multiple project files, ensuring consistency and ease of use.

### JSON File: wifi_info.json
The wifi_info.json file stores essential Wi-Fi configuration details required for the Lucid Dreaming Portable Prototype project. Below are the key attributes of the JSON file:

#### SSID:
Represents the name of the Wi-Fi network (Service Set Identifier) that the Raspberry Pi connects to.
Example: "ssid": "Monash WiFi"

#### Password:
Contains the password required for accessing the Wi-Fi network specified by the SSID.
Example: "password": "MonashPassword12345"

#### IP Address:
Stores the IP address assigned to the Raspberry Pi within the Wi-Fi network.
Example: "ip_address": "192.168.1.1"

This JSON file serves as a central repository for storing Wi-Fi configuration details, facilitating easy access and update of essential network settings used by the Lucid Dreaming Prototype project.

## Folder: Arduino Libraries
The "Arduino Libraries" folder contains the libraries needed for Arduino IDE and the ESP8266 device codes to run. Below are the key aspects of this folder:

### Purpose:
This folder houses the libraries needed for the Arduino IDE to run the device codes

### Contents:
Includes the Adafruit_NeoPixel.h, ArduinoJson.h, ESP8266HTTPClient.h, ESP8266WiFi.h, and SoftwareSerial.h libraries folders

### Integration:
These libraries should be copied into the Arduino Libraries folder of the Pi so that the device codes would work.

## Folder: Command-Scripts
The "Command-Scripts" folder contains Python scripts responsible for executing various commands and functionalities within the Lucid Dreaming Portable Prototype project. Below are the key aspects of this folder:

### Purpose:
This folder houses Python scripts that handle command execution, communication with devices, and other operational tasks within the project.

### Contents:
It typically includes scripts such as AirPump.py, AudioStimulus.py, BlockCommands.py, CommandSender.py, GVS_Stimulus.py, TACS_Stimulus.py, UnblockCommands.py, and VisualStimulus.py.
These scripts may interact with hardware components, process sensory inputs, or control stimulus delivery based on predefined commands.

### Functionality:
Each Python script serves a specific purpose related to the project's functionality, such as controlling air pumps, generating audio stimuli, managing visual stimuli, and facilitating communication with devices.

### Integration:
The main script being used is the "CommandSender.py" which controls the system autonomously when activated. The other scripts are used to test the individual components of the system when needed for debugging the system.

## Folder: Devices
The "Devices" folder contains Arduino sketches (.ino files) representing firmware programs for various hardware devices used in the Lucid Dreaming Portable Prototype project. Here's an overview of this folder:

### Purpose:
This folder stores firmware code written in Arduino language (based on C/C++) for programming microcontroller-based devices used within the project.

### Contents:
It typically includes sketches such as Device_1-Emergency_Button.ino, Device_2-LED.ino, Device_3-Speakers.ino, Device_4-Bubble_Motor.ino, Device_5-GVS.ino, and Device_6-TACS.ino, among others.
Each sketch corresponds to a specific hardware device or component and contains instructions for its operation, input/output handling, and communication protocols.

### Functionality:
These Arduino sketches define the behavior and functionality of individual devices, such as emergency buttons, LEDs, speakers, motors, galvanic vestibular stimulators (GVS), and transcranial alternating current stimulators (TACS).

### Integration:
Once uploaded to respective microcontrollers (e.g., Arduino boards), these sketches enable the devices to perform predefined actions, respond to commands, and interact with other system components.

# New Pi Setup Procedure

## Setting Up Your New Raspberry Pi
With your new Raspberry Pi, you need to install Raspbian OS onto the SD card by using the Raspberry Pi Imager to install Raspberry Pi OS to a microSD card, for use on your Raspberry Pi.

https://www.raspberrypi.com/software/

Once installed, you can boot the Pi with the newly loaded microSD with the OS, and set up the Pi accordingly.
The common naming conventions and passwords used when setting up Raspberry Pis for the lab is as follows:

username: xgl-monash
password: abc

## Installing Dependencies
Once the new Raspberry Pi is booted, the dependencies needed for the server needs to be downloaded, which is as follows

### Update the Pi
```bash
sudo apt-get update
sudo apt-get upgrade
```

### Install python
```bash
sudo apt-get install python3 python3-pip
```

### Install node.js
```bash
sudo apt-get install node.js
```

### Install npm
```bash
sudo apt-get install npm
```

### Install typescript
```bash
sudo npm install -g typescript
```

### Install python packages
The Requests module can be installed using the following code below
```bash
sudo apt install python3-requests
```

However, to install the playsound and brainflow module, you would need to use a virtual environment, which is done by
```bash
python3 -m venv path/to/venv
```
where you replace 'path/to/venv' with the desired location for your virtual environment

Then avtivate it by running
```bash
source path/to/venv/bin/activate
```
This command activates the virtual environment and changes your prompt to indicate that the environment is active.

With the virtual environment activated, you can now install the Python package using pip. Run the following command:
```bash
pip install playsound
pip install brainflow
```

After the installation is complete, you can verify that the package is installed correctly by running:
```bash
pip list
```
This command will display a list of installed packages in the virtual environment.

When you're done working in the virtual environment, you can deactivate it by running the following command:
```bash
deactivate
```
This command will return you to your original shell session.

### Install lxterminal
```bash
sudo apt-get install lxterminal
```

## Cloning Server Codes
To clone the server codes from the Git repository, a public SSH key needs to be generated and added to the xgl.monash@gmail.com Github account.
To do this:
1. open a terminal in the Pi and enter
```bash
ssh-keygen -t rsa -C xgl.monash@gmail.com
```
Accept the default values by pressing enter when prompted, and the SSH key should be generated. 

2. Navigate to the .ssh folder in the user folder of the Pi. In there, would be the SSH key which typically begins with "ssh-rsa". Copy the key and add it to the Github account. This is done by navigating on Github to Settings > SSH and GPG keys > New SSH key. Add the new SSH key and give it a title before saving it by pressing "Add SSH key".

Once the SSH key is added, you can now clone the server codes onto the Pi. Navigate to the location you wish to store the Server code folder and open the terminal of that path(as standard practice, the lab usually sets the path to /home/"user"), where user is the username of the Pi. In this terminal, enter 
```bash
git clone git@github.com:Exertion-Games-Lab/LuciEntry.git
```

The codes should now be cloned into your Pi. Lastly, open the terminal with the path to "LuciEntry" and enter
```bash
chmod +x start.sh
```
This gives the shell file execute permissions.

You might also want to open a terminal at the Server directory of the LuciEntry folder and run:
```bash
npm install
```
to install all the necessary dependencies that you may have missed.

Once that is done, the project codes are ready to be used.

## Installing Arduino IDE and relevant libraries
Install the Arduino IDE in the Pi from 
https://www.arduino.cc/en/software
Download the latest version of Arduino IDE for Linux ARM 64 bits.
and follow the instructions here to extract and install it: https://www.raspberrypi-spy.co.uk/2020/12/install-arduino-ide-on-raspberry-pi/

Add the ESP8266 Board into the Arduino IDE
https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/

Copy the necessary Arduino libraries into the library folder of the Arduino IDE. 
This is done by navigating to  the "LuciEntry>Arduino Libraries" folder, copying the folders, and pasting it into the "Arduino>libraries" folder in your Pi.

# User Guide 
The following section contains the details for using the server on a Raspberry Pi after it is installed.

[User Guide Diagram](https://github.com/Exertion-Games-Lab/LuciEntry/blob/main/UserGuide.drawio.png)
Above shows the brief diagram of the walkthrough in starting the server for the prototype.

## Step 1: Open a terminal with the path to the "LuciEntry" Folder
To do this, open the file manager and navigate to the LuciEntry folder which was cloned from Git. Right-click and select "Open in Terminal"

## Step 2: Run Configure WiFi python program
On the opened terminal, run the configure WiFi program by typing:
```bash
python configure_wifi.py
```
When the program runs, it will present 2 prompts to the user:
  1.  "Warning: The connected WiFi SSID 'your_wifi' does not match the stored WiFi SSID 'stored_wifi'. Do you want to change WiFi details? (y/n)"
    
  2.  "Connected WiFi SSID: 'your_wifi'"

### Prompt #1
when this prompt appears, it means the current WiFi the Pi is connected to, is not the same as the one stored on the system. When this prompt appears, users have 2 options
  1. Option 1 (y): Users can update the wifi details to the one currently connected to the Pi. Users are then prompted to enter the WiFi password twice, which would then update the server files with the new WiFi details and present the prompt "Changes were made. Please connect the devices to the Pi and upload the newly configured codes before running the server.", which alerts users that files have been updated and the new code files need to be uploaded into the ESP8266s boards, as outlined in the steps in [Prompt #2-2](#prompt-2-2). When the devices codes have been uploaded to each device's ESP8266 board, the server is ready to be started, following the steps outlined in [Step 3](#step-3-start-server)

  2. Option 2 (n): Users can choose to not update the files, and instead connect to the wifi that is stored in the system. 

### Prompt #2
When this prompt appears, it means the current WiFi the Pi is connected to, is the same as the one stored on the system. When this prompt appears, 2 subsequent prompts will appear:
  1.  "No changes were made. Server is ready to run."

  2.  "Changes were made. Please connect the devices to the Pi and upload the newly configured codes before running the server."

#### Prompt #2-1
When this prompt appears, it means that all the files are up to date and the server is ready for start-up. You can then proceed to [Step 3](#step-3-start-server)

#### Prompt #2-2
When this prompt appears, it means the command scripts and device codes have been updated and users need to upload the new codes to the devices.
You can upload the device codes using the Arduino IDE on the Raspberry Pi. This is done by navigating to the folder "LuciEntry > Devices". In this folder, there are folders for each devices. Within each folder, is an .ino file which is the arduino code which you would upload into the ESP8266s. Opening the .ino file would open the Arduino IDE with the code file you opened. In the Arduino IDE, select the correct "Boards" and "Ports" in the "Tools" section, before pressing upload (the arrow-right button) to upload the code to the ESP8266 boards. When the devices codes have been uploaded to each device's ESP8266 board, the server is ready to be started, following the steps outlined in [Step 3](#step-3-start-server)

## Step 3: Start Server
In the same terminal, you can enter:

```bash
./start.sh
```
to start up the server, and the respective python programs needed for the system.
This should open up 3 terminals called "Server", "Speaker" and "Command Sender".
