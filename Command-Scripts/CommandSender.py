import requests
import threading
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Devices/detector'))
import Detector

IP_ADDRESS = '192.168.1.118'
base_url = f'http://{IP_ADDRESS}:8080'

class Parameter(object):
    pass

# Define commands for different stimuli
# Define LDI commands with 10 seconds duration every 20 seconds
def send_LDI_commands():
    print('Sending LDI commands')
    # 1 Hz Red LED Light
    lightPayload = {'brightness': 30, 'frequency': 1, 'duration': 10000, 'colour': {'r': 255, 'g': 0, 'b': 0}}
    requests.post(f'{base_url}/command/2/VisualStimulus', json=lightPayload)
    # 40 Hz tACS (Transcranial Alternating Current Stimulation)
    tacsPayload = {'frequency': 40, 'millis': 10000, 'intensity': 100}
    requests.post(f'{base_url}/command/5/GVS_Stimulus', json=tacsPayload)
    # Theta binaural beat with white noise
    soundPayload = {'filename': 'THETA.mp3', 'volume': 30, 'duration': 10000}
    requests.post(f'{base_url}/command/3/Audio', json=soundPayload)

def send_Diving_commands():
    print('Sending Diving commands')
    soundPayload = {'filename': 'water.mp3', 'volume': 30, 'duration': 10000}
    requests.post(f'{base_url}/command/3/Audio', json=soundPayload)
    lightPayload = {'brightness': 30, 'colour': {'r': 0, 'g': 0, 'b': 255}}
    requests.post(f'{base_url}/command/2/VisualStimulus', json=lightPayload)
    requests.post(f'{base_url}/command/4/AirPump', {})
    requests.post(f'{base_url}/command/5/GVS_Stimulus', {})

def repeat_send_commands(commandParameters, command, interval):
    cnt = interval
    while not commandParameters.isInterrupt:
        if cnt >= interval:
            cnt = 0
            command()
            print('Enter anything to interrupt')
        else:
            cnt += 1
            time.sleep(1)
    print('Stop repeating commands')

# Send induction stimuli every 20 seconds
def send_induction_stimuli(commandParameters):
    while not commandParameters.isInterrupt:
        if commandParameters.sleep_stage == 'REM_PERIOD':
            send_LDI_commands()
            print('Induction Stimuli Sent')
        else:
            print('Exited REM Stage. Stopping Induction Stimuli.')
            commandParameters.isInterrupt = True
            break
        time.sleep(20)

def interactive_mode():
    while True:
        print('Enter a number for the desired stimuli:')
        print('1. LDI stimuli')
        print('2. Diving stimuli')
        mode = input()
        commandParameters = Parameter()
        commandParameters.isInterrupt = False
        if mode == '1':
            print('Start LDI')
            thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_LDI_commands, 20))
            thread.daemon = True
            thread.start()
        elif mode == '2':
            print('Start Diving')
            thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_Diving_commands, 10))
            thread.daemon = True
            thread.start()
        else:
            print('Invalid Input')
        while True:
            userKeyInput = input()
            if userKeyInput:
                commandParameters.isInterrupt = True
                break

def timer_mode():
    print('Start Countdown')
    time.sleep(700)
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_LDI_commands, 30))
    thread.daemon = True
    thread.start()
    time.sleep(120)
    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False
    thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_Diving_commands, 10))
    thread.daemon = True
    thread.start()
    while True:
        userKeyInput = input()
        if userKeyInput:
            commandParameters.isInterrupt = True
            break

def detector_mode():
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    commandParameters.induction = False
    commandParameters.sleep_stage = 'Awake'
    thread = threading.Thread(target=Detector.detection, args=(commandParameters, 'OPEN_BCI'))
    thread.daemon = True
    thread.start()

    # Wait until the REM period starts
    while commandParameters.sleep_stage != 'REM_PERIOD':
        time.sleep(1)
    print('TIME FOR INDUCTION!')

    commandParameters.isInterrupt = False
    commandParameters.induction = True

    print('Start Induction Stimuli every 20 seconds')
    induction_thread = threading.Thread(target=send_induction_stimuli, args=(commandParameters,))
    induction_thread.daemon = True
    induction_thread.start()

    while True:
        userKeyInput = input()
        if userKeyInput:
            commandParameters.isInterrupt = True
            break

    print('Start Diving Stimuli')
    commandParameters.isInterrupt = False
    diving_thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_Diving_commands, 10))
    diving_thread.daemon = True
    diving_thread.start()

    while True:
        userKeyInput = input()
        if userKeyInput:
            commandParameters.isInterrupt = True
            break

def main():
    while True:
        print('Enter a number for mode:')
        print('1. Interactive mode')
        print('2. Timer mode')
        print('3. Detector mode')
        print('Else: End')
        mode = input()
        if mode == '1':
            interactive_mode()
        elif mode == '2':
            timer_mode()
        elif mode == '3':
            detector_mode()
        else:
            print('End the program')
            break

if __name__ == '__main__':
    main()