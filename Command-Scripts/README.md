# Command Scripts Folder
This folder contains Python scripts responsible for sending commands to the LuciEntry Prototype server. These scripts are used to control various aspects of the system, such as visual stimuli, audio stimuli, and other commands.

## Structure and Architecture
Each command script follows a similar structure and architecture to maintain consistency and ease of development. Below is an explanation of the general code structure and architecture:

### Imports: 
The script begins with importing necessary modules. The requests module is used for making HTTP requests to the server, and sys module is used for accessing command-line arguments.

### Main Execution: 
The if __name__ == '__main__': block ensures that the script is executed only when it's directly run, not when it's imported as a module.

### Server Configuration: 
The IP address and base URL of the LuciEntry Prototype server are defined. These values are used to construct the URL for sending commands.

### Command Parameters: 
Parameters related to the command are defined, such as brightness and RGB values for visual stimuli. These parameters can be customized either by passing them as command-line arguments or using default values.

### Payload Construction: 
A payload dictionary is created to encapsulate the command parameters. This payload is then sent as JSON data in the HTTP POST request to the server.

### HTTP POST Request: 
The script uses the requests.post() function to send the command to the server. The constructed URL and payload are passed as arguments to this function.
