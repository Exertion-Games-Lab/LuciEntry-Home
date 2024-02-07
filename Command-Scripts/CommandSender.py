import requests
import threading
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Devices/detector'))
import Detector

IP_ADDRESS = "192.168.1.26"
base_url = f"http://{IP_ADDRESS}:8080"

class Parameter(object):
    pass

def send_LDI_commands():
    print("sending LDI commands")
    soundPayload = {
        'filename': "THETA.mp3",
        'volume': 30,
        'duration': 10000
    }
    requests.post(f"{base_url}/command/2/Audio", json=soundPayload)

    
    lightPayload = {
        'brightness': 30,
        'colour': {
            'r': 255,
            'g': 0,
            'b': 0
        }
    }
    requests.post(f"{base_url}/command/1/VisualStimulus", json=lightPayload)

def send_Diving_commands():
    print("sending Diving commands")
    requests.post(f"{base_url}/command/1/BlueVisualStimulus", {})
    # requests.post(f"{base_url}/command/2/BubbleAudioStimulus", {})
    requests.post(f"{base_url}/command/2/WaterAudioStimulus", {})
    requests.post(f"{base_url}/command/3/AirPumpStimulus", {})
    requests.post(f"{base_url}/command/4/GVSStimulus", {})

def repeat_send_commands(commandParameters,command,interval):
    #interval = 10
    cnt = interval
    while(commandParameters.isInterrupt==False):
        if(cnt>=interval):
            cnt = 0
            command()
            print("Enter anythings to interrupt")
        else:
            cnt +=1
            time.sleep(1)
    print("stop repeating commands")


def interactive_mode():
    while(True):
        #read mode
        print("Enter a number for the desired stimuli:")
        print("1. LDI stimuli")
        print("2. Diving stimuli")
        mode = input()
        commandParameters = Parameter()
        commandParameters.isInterrupt = False
        isInterrupt = False
        if mode =='1':
                print("start LDI")
                thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_LDI_commands,30))
                thread.daemon = True
                thread.start()
        elif mode =='2':
                print("start diving")
                thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_Diving_commands,10))
                thread.daemon = True
                thread.start()
        else:
                print("error type")

        #read input to interrupt
        while True:
            userKeyInput = input()
            if(userKeyInput !=""):
                commandParameters.isInterrupt = True
                break

def timer_mode():
    #time.sleep(10)
    print("start counting down")
    time.sleep(700)
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_LDI_commands,30))
    thread.daemon = True
    thread.start()
    #time.sleep(50)
    time.sleep(120)
    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False
    thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_Diving_commands,10))
    thread.daemon = True
    thread.start()
    #read input to interrupt
    while True:
        userKeyInput = input()
        if(userKeyInput !=""):
            commandParameters.isInterrupt = True
            break


def detector_mode():
    commandParameters = Parameter()
    commandParameters.isInterrupt = False

    #REM detection
    commandParameters.sleep_stage = 'Awake'
    isInterrupt = False
    thread = threading.Thread(target = detector.detection,args=(commandParameters, False))
    thread.daemon = True
    thread.start()
    cnt = 0
    while cnt<=60:
        time.sleep(1)
        #print(commandParameters.sleep_stage)
        if commandParameters.sleep_stage == "REM":
            cnt+=1
    print("TIME FOR Induction!")
    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False


    #induction stimuli
    print("start induction")
    thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_LDI_commands,30))
    thread.daemon = True
    thread.start()

    #read input to interrupt
    while True:
        userKeyInput = input()
        if(userKeyInput !=""):
            commandParameters.isInterrupt = True
            break

    commandParameters.isInterrupt = True
    time.sleep(2)
    commandParameters.isInterrupt = False

    #diving func
    print("start diving")
    thread = threading.Thread(target = repeat_send_commands,args=(commandParameters,send_Diving_commands,10))
    thread.daemon = True
    thread.start()
    #read input to interrupt
    while True:
        userKeyInput = input()
        if(userKeyInput !=""):
            commandParameters.isInterrupt = True
            break




def main():
    while True:
        #read mode
        print("Enter a number for mode:")
        print("1. interactive mode")
        print("2. timer mode")
        print("3. detector mode")
        print("else: end")
        mode = input()
        if (mode =='1'):
            interactive_mode()
        elif(mode =='2'):
            timer_mode()
        elif(mode =='3'):
            detector_mode()
        else:
            print("End the program")
            break





if __name__ == "__main__":
    main()
