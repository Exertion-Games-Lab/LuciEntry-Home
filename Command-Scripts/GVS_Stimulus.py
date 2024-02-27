import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.1.118'
    base_url = f'http://{IP_ADDRESS}:8080'
    millis = 10000
    intensity = 100
    if len(sys.argv) >= 3:
        millis = int(sys.argv[1])
        intensity = int(sys.argv[2])
    payload = {'millis': millis, 'intensity': intensity}
    requests.post(f'{base_url}/command/5/GVS_Stimulus', json=payload)