import requests
import sys
if __name__ == '__main__':
    IP_ADDRESS = '192.168.43.47'
    base_url = f'http://{IP_ADDRESS}:8080'
    filename = 'ALPHA.mp3'
    volume = 100
    duration = 10000
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    if len(sys.argv) == 3:
        filename = sys.argv[1]
        volume = int(sys.argv[2])
    if len(sys.argv) >= 4:
        filename = sys.argv[1]
        volume = int(sys.argv[2])
        duration = int(sys.argv[3])
    payload = {'filename': filename, 'volume': volume, 'duration': duration}
    requests.post(f'{base_url}/command/3/Audio', json=payload)