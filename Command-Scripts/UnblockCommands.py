import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.43.196'
    base_url = f'http://{IP_ADDRESS}:8080'
    requests.post(f'{base_url}/unblockCommands')