import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.1.118'
    base_url = f'http://{IP_ADDRESS}:8080'
    millis = 10000
    intensity = 100
    frequency = 100
    if len(sys.argv) >= 4:
        millis = int(sys.argv[1])
        intensity = int(sys.argv[2])
        frequency = int(sys.argv[3])
    payload = {'millis': millis, 'intensity': intensity, 'frequency': frequency}
    requests.post(f'{base_url}/command/6/TACS_Stimulus', json=payload)