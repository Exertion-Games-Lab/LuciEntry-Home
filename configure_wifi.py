import json
import subprocess
import getpass
import ast
import os

logo = """
         ::::::        
        ::::::::       
        ::::::::  :::: 
    ::   ::::::  ::::::
  :::::::       :::::::
  :::::::::-   ::::::: 
    :::::::::::::::::: 
       :::::::::::::   
         ::::::::::    
         :::::::::     
       :::::::::::::   
    :::::::::::::::::  
::::::::::::  :::::::: 
:::::::::      ::::::::
::::::          :::::::
                 ::::::
                 ::::::

"""

def get_current_wifi_ssid():
    try:
        result = subprocess.run(["iwgetid", "-r"], capture_output=True, text=True)
        ip_addresses = result.stdout.strip().split()
        ipv4_addresses = [address for address in ip_addresses if '.' in address]
        return ipv4_addresses[0] if ipv4_addresses else None
    except Exception as e:
        print(f"Error obtaining current WiFi SSID: {e}")
        return None

def get_ip_address():
    try:
        result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
        ip_address = result.stdout.strip()
        return ip_address
    except Exception as e:
        print(f"Error obtaining IP address: {e}")
        return None

def find_folder(root_path, target_folder):
    for dirpath, dirnames, filenames in os.walk(root_path):
        if target_folder in dirnames:
            return os.path.join(dirpath, target_folder)
    return None

def find_file_in_folder(folder_path, target_file):
    for dirpath, dirnames, filenames in os.walk(folder_path):
        if target_file in filenames:
            return os.path.join(dirpath, target_file)
    return None

def update_pyscript_with_wifi_info(script_path, wifi_info):
    with open(script_path, 'r') as file:
        script_content = file.read()

    # Parse the script content into an AST
    tree = ast.parse(script_content)

    # Define the variables you want to update
    variables_to_update = {
        'SSID': wifi_info.get('ssid', ''),
        'PASSWORD': wifi_info.get('password', ''),
        'IP_ADDRESS': wifi_info.get('ip_address', '')
    }

    changes_made = False  # Flag to track changes

    # Traverse the AST and update variable values
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in variables_to_update:
                    # Check if the value needs updating
                    if node.value.s != variables_to_update[target.id]:
                        changes_made = True
                        # Update the variable value
                        node.value = ast.Str(s=variables_to_update[target.id])

    # Reconstruct the script content from the modified AST
    updated_script = ast.unparse(tree)

    with open(script_path, 'w') as file:
        file.write(updated_script)

    return changes_made

def update_arduino_script_with_wifi_info(script_path, wifi_info):
    with open(script_path, 'r') as file:
        script_lines = file.readlines()

    changes_made = False  # Flag to track changes

    for i, line in enumerate(script_lines):
        # Check for the presence of SSID, PASSWORD, and IP_ADDRESS variables
        if 'const char* SSID =' in line:
            current_ssid = line.split('"')[1]  # Extract the current SSID value
            if current_ssid != wifi_info["ssid"]:
                script_lines[i] = f'const char* SSID = "{wifi_info["ssid"]}";\n'
                changes_made = True
        elif 'const char* PASSWORD =' in line:
            current_password = line.split('"')[1]  # Extract the current PASSWORD value
            if current_password != wifi_info["password"]:
                script_lines[i] = f'const char* PASSWORD = "{wifi_info["password"]}";\n'
                changes_made = True
        elif 'const String IP_ADDRESS =' in line:
            current_ip_address = line.split('"')[1]  # Extract the current IP_ADDRESS value
            if current_ip_address != wifi_info["ip_address"]:
                script_lines[i] = f'const String IP_ADDRESS = "{wifi_info["ip_address"]}";\n'
                changes_made = True

    if changes_made:
        with open(script_path, 'w') as file:
            file.writelines(script_lines)

    return changes_made

def main():
    # List of files to update
    root_path = "/home/"
    target_folder = "LuciEntry-Home"
    main_folder_path = find_folder(root_path, target_folder)
    target_files_py = ["AirPump.py","AudioStimulus.py","BlockCommands.py","CommandSender.py","GVS_Stimulus.py","TACS_Stimulus.py","UnblockCommands.py","VisualStimulus.py","Device_3-Speakers.py"]
    target_files_ino = ["Device_1-Emergency_Button.ino","Device_2-LED.ino","Device_3-Speakers.ino","Device_4-Bubble_Motor.ino","Device_5-GVS.ino","Device_6-TACS.ino"]

    py_file_paths = []
    for file in target_files_py:
        result_paths = find_file_in_folder(main_folder_path, file)
        py_file_paths.append(result_paths)

    ino_file_paths = []
    for file in target_files_ino:
        result_paths = find_file_in_folder(main_folder_path, file)
        ino_file_paths.append(result_paths)

    changes_made = False  # Flag to track changes

    #Welcome message
    print(logo)
    print("Welcome to Exertion Games Lab, Lucid Dreaming Portable Prototype")

    # Read existing WiFi information from the JSON file
    with open('wifi_info.json', 'r') as file:
        wifi_info = json.load(file)

    current_ssid = get_current_wifi_ssid()

    if current_ssid != wifi_info['ssid']:
        print(f"Warning: The connected WiFi SSID '{current_ssid}' does not match the stored WiFi SSID '{wifi_info['ssid']}'.")
        change_wifi_confirmation = input("Do you want to change WiFi details? (y/n): ").lower()

        if change_wifi_confirmation == 'n':
            print(f"Please connect to this Wifi: '{wifi_info['ssid']}'.")
            return
        
        elif change_wifi_confirmation == 'y':
            while True:
                new_password = getpass.getpass(f"Enter the WiFi password for {current_ssid}: ")
                confirm_password = getpass.getpass(f"Confirm the WiFi password for {current_ssid}: ")
                if new_password == confirm_password and len(new_password) > 0:
                    # Update WiFi information in the JSON file
                    wifi_info['ssid'] = current_ssid
                    wifi_info['password'] = new_password

                    ip_address = get_ip_address()

                    if ip_address:
                        wifi_info['ip_address'] = ip_address

                    with open('wifi_info.json', 'w') as file:
                        json.dump(wifi_info, file, indent=2)

                        print("WiFi configuration updated!")
                        print("Updating files with new WiFi details.")

                    with open("wifi_info.json", "r") as json_file:
                        wifi_info = json.load(json_file)

                        # Update command script files
                        for file_path in py_file_paths:
                            changes_made |= update_pyscript_with_wifi_info(file_path, wifi_info)

                        # Update device files
                        for file_path in ino_file_paths:
                            changes_made |= update_arduino_script_with_wifi_info(file_path, wifi_info)

                        if changes_made:
                            print('Changes were made. Please connect the device boxes to the pi and upload the newly configured codes before running the server.')
                        else:
                            print('No changes were made. Server is ready to run.')
                    break
                else:
                    print("Passwords do not match! Please try again.")
        else:
            print("Invalid input. Please run the script again.")
            return
    else:
        print(f"Connected WiFi SSID: {current_ssid}")
        with open("wifi_info.json", "r") as json_file:
            changes_made = False  # Flag to track changes

            # Update command script files
            for file_path in py_file_paths:
                changes_made |= update_pyscript_with_wifi_info(file_path, wifi_info)

            # Update device files
            for file_path in ino_file_paths:
                changes_made |= update_arduino_script_with_wifi_info(file_path, wifi_info)

            if changes_made:
                print('Changes were made. Please connect the device boxes to the pi and upload the newly configured codes before running the server.')
                return 1  # Changes were made
            else:
                print('No changes were made. Server is ready to run.')
                return 0  # No changes were made

if __name__ == "__main__":
    main()
