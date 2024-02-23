import requests
import threading
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Devices/detector'))
import Detector
IP_ADDRESS = '192.168.85.231 2001:8004:15a0:40eb:4f60:637b:a455:de30'
base_url = f'http://{IP_ADDRESS}:8080'

class Parameter(object):
    pass

def send_LDI_commands():
    print('sending LDI commands')
    soundPayload = {'filename': 'THETA.mp3', 'volume': 30, 'duration': 10000}
    requests.post(f'{base_url}/command/3/Audio', json=soundPayload)
    lightPayload = {'brightness': 30, 'colour': {'r': 255, 'g': 0, 'b': 0}}
    requests.post(f'{base_url}/command/2/VisualStimulus', json=lightPayload)
    tacsPayload = {'millis': 10000, 'intensity': 100}
    requests.post(f'{base_url}/command/5/GVS_Stimulus', json=tacsPayload)

def send_Diving_commands():
    print('sending Diving commands')
    soundPayload = {'filename': 'water.mp3', 'volume': 30, 'duration': 10000}
    requests.post(f'{base_url}/command/3/Audio', json=soundPayload)
    lightPayload = {'brightness': 30, 'colour': {'r': 0, 'g': 0, 'b': 255}}
    requests.post(f'{base_url}/command/2/VisualStimulus', json=lightPayload)
    requests.post(f'{base_url}/command/4/AirPump', {})
    requests.post(f'{base_url}/command/5/GVS_Stimulus', {})

def repeat_send_commands(commandParameters, command, interval):
    cnt = interval
    while commandParameters.isInterrupt == False:
        if cnt >= interval:
            cnt = 0
            command()
            print('Enter anythings to interrupt')
        else:
            cnt += 1
            time.sleep(1)
    print('stop repeating commands')

def interactive_mode():
    while True:
        print('Enter a number for the desired stimuli:')
        print('1. LDI stimuli')
        print('2. Diving stimuli')
        mode = input()
        commandParameters = Parameter()
        commandParameters.isInterrupt = False
        isInterrupt = False
        if mode == '1':
            print('start LDI')
            thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_LDI_commands, 20))
            thread.daemon = True
            thread.start()
        elif mode == '2':
            print('start diving')
            thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_Diving_commands, 10))
            thread.daemon = True
            thread.start()
        else:
            print('error type')
        while True:
            userKeyInput = input()
            if userKeyInput != '':
                commandParameters.isInterrupt = True
                break

def timer_mode():
    print('start counting down')
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
        if userKeyInput != '':
            commandParameters.isInterrupt = True
            break

def detector_mode():
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    commandParameters.induction = False
    commandParameters.sleep_stage = 'Awake'
    isInterrupt = False
    thread = threading.Thread(target=Detector.detection, args=(commandParameters, 'OPEN_BCI'))
    thread.daemon = True
    thread.start()
    while commandParameters.sleep_stage != 'REM_PEROID':
        time.sleep(1)
    print('TIME FOR Induction!')
    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False
    commandParameters.induction = True
    print('start induction')
    thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_LDI_commands, 20))
    thread.daemon = True
    thread.start()
    while True:
        userKeyInput = input()
        if userKeyInput != '':
            commandParameters.isInterrupt = True
            break
    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False
    print('start diving')
    thread = threading.Thread(target=repeat_send_commands, args=(commandParameters, send_Diving_commands, 10))
    thread.daemon = True
    thread.start()
    while True:
        userKeyInput = input()
        if userKeyInput != '':
            commandParameters.isInterrupt = True
            break

def main():
    while True:
        print('Enter a number for mode:')
        print('1. interactive mode')
        print('2. timer mode')
        print('3. detector mode')
        print('else: end')
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