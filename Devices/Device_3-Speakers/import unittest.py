import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import requests
import asyncio
import time

import platform

# Code to be tested (usually this would be imported)
from playsound import playsound



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
        
######
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
######

async def playSound(soundName: str, durationMilliSeconds: int,volume: int):
    durationSeconds = durationMilliSeconds / 1000
    print(f"Playing sound {soundName} at volume {volume}")
    
    try:
        await set_volume(volume)
        playsound(f'./mp3/{soundName}', block=False)
        await customSleep(durationSeconds)
    except:
        print(f'No file with name {soundName}')





class TestYourModule(unittest.TestCase):

    @patch('Device_3_Speakers.requests.get')
    def test_fetch_next_command(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'command': {'instructions': [{'code': 3, 'payload': {'soundName': 'test', 'durationMillis': 1000}}]}}
        mock_get.return_value = mock_response

        command = fetch_next_command('device1', 'http://localhost:8080')
        self.assertIsNotNone(command)
        self.assertEqual(command['instructions'][0]['code'], 3)

    @patch('Device_3_Speakers.playsound')
    async def test_execute_instruction(self, mock_playsound):
        instruction = {'code': 3, 'payload': {'soundName': 'test', 'durationMillis': 1000}}
        await execute_instruction(instruction)
        mock_playsound.assert_called_once_with('./mp3/test/', block=False)

    @patch('Device_3_Speakers.fetch_next_command')
    @patch('Device_3_Speakers.execute_instruction')
    async def test_fetch_and_execute(self, mock_execute_instruction, mock_fetch_next_command):
        mock_fetch_next_command.return_value = {'instructions': [{'code': 3, 'payload': {'soundName': 'test', 'durationMillis': 1000}}]}
        await fetch_and_execute('device1', 'http://localhost:8080')
        mock_execute_instruction.assert_called_once()

    @patch('Device_3_Speakers.requests.get')
    async def test_checkKillCommands(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'BLOCK_COMMANDS': True}
        mock_get.return_value = mock_response

        result = await checkKillCommands()
        self.assertTrue(result)

    async def test_customSleep(self):
        with patch('Device_3_Speakers.checkKillCommands', return_value=False):
            await customSleep(1)
            # Check no exception is raised

    @patch('Device_3_Speakers.playsound')
    async def test_playSound(self, mock_playsound):
        await playSound('test', 1000, 10)
        mock_playsound.assert_called_once_with('./mp3/test/10', block=False)

if __name__ == '__main__':
    unittest.main()