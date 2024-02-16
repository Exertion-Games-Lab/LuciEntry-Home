import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.43.47'
    base_url = f'http://{IP_ADDRESS}:8080'
    brightness = 50
    red = 255
    green = 0
    blue = 0
    if len(sys.argv) >= 5:
        brightness = int(sys.argv[1])
        red = int(sys.argv[2])
        green = int(sys.argv[3])
        blue = int(sys.argv[4])
    elif len(sys.argv) <= 4 and len(sys.argv) > 1:
        brightness = int(sys.argv[1])
    payload = {'brightness': brightness, 'colour': {'r': red, 'g': green, 'b': blue}}
    requests.post(f'{base_url}/command/2/VisualStimulus', json=payload)