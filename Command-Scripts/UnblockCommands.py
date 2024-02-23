import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.85.231 2001:8004:15a0:40eb:4f60:637b:a455:de30'
    base_url = f'http://{IP_ADDRESS}:8080'
    requests.post(f'{base_url}/unblockCommands')