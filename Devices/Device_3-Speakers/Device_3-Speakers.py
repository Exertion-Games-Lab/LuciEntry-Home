import requests
from playsound import playsound
import time
import asyncio
import platform
import os

def fetch_next_command(device_id, base_url):
    try:
        response = requests.get(f'{base_url}/command/{device_id}')
        if response.json() == {}:
            return None
        if response.status_code == 200:
            return response.json()['command']
        else:
            print(f'Failed to fetch next command for device {device_id}. Status code: {response.status_code}')
            return None
    except:
        return None

async def execute_instruction(instruction):
    code = instruction['code']
    payload = instruction['payload']
    
    if code == 3:
        print(f'Executing instruction 3 with payload {payload}')
        soundName = payload['soundName']
        durationMilliSeconds = payload['durationMillis']
        volume = payload['volume']
        await playSound(soundName, durationMilliSeconds,volume)
    else:
        print(f'Unknown instruction code {code}. Ignoring.')

async def fetch_and_execute(device_id, base_url):
    command = fetch_next_command(device_id, base_url)
    if command is not None:
        for instruction in command['instructions']:
            await execute_instruction(instruction)
    else:
        time.sleep(5)

async def checkKillCommands() -> bool:
    response = requests.get('http://localhost:8080/blockCommands')
    if response.json() == {}:
        return False
    if response.status_code == 200:
        return response.json()['BLOCK_COMMANDS']
    else:
        return checkKillCommands()

async def customSleep(time: int):
    for _ in range(round((time + 1) * 10)):
        if await checkKillCommands():
            return
        await asyncio.sleep(0.1)
        
async def set_volume(volume: int):
    system = platform.system()
    if system == 'Windows':
        os.system(f"nircmd.exe setsysvolume {volume * 65535 // 100}")
    elif system == 'Darwin':  # macOS
        os.system(f"osascript -e 'set volume output volume {volume}'")
    elif system == 'Linux':
        os.system(f"amixer -D pulse sset Master {volume}%")
    else:
        print("Unsupported OS")

async def playSound(soundName: str, durationMilliSeconds: int,volume: int):
    durationSeconds = durationMilliSeconds / 1000
    print(f"Playing sound {soundName} at volume {volume}")
    try:
        await set_volume(volume)
        playsound(f'./mp3/{soundName}', block=False)
        await customSleep(durationSeconds)
    except:
        print(f'No file with name {soundName}')

async def main():
    while True:
        await fetch_and_execute(3, 'http://localhost:8080')
        await customSleep(1)
asyncio.run(main())
