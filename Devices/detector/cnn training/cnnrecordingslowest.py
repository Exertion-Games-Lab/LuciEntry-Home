import argparse
from datetime import date
import time
import json
import numpy as np 
# import pickle
# import yasa
# from mne import create_info
# from mne.io import RawArray
# from flask import Flask, jsonify, request
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, WindowOperations, DetrendOperations, FilterTypes, AggOperations
# our own graph drawer
#import GraphDrawer
from threading import Thread
import os


class Parameter(object):
    pass

# A global variable to store the REM state
rem_state = {}

class Detector:
    def __init__(self, board_name = "SYNTHETIC", commandParameters = None):
        ## Init board and streaming params 
        self.params = BrainFlowInputParams()
        

        # Identify serial port location of Wifi dongle
        # if you are using windows or mac, you will need to change below to your specific serial port directiory
        # if you are using a raspberry pi, it should work without needing to modify it
        # if you are using synthetic data, this dosent matter as it wont get used
        if board_name =="SYNTHETIC":
            # Synthetic for generating fake data, cyton for using the actual real board
            self.board_id = BoardIds.SYNTHETIC_BOARD.value
        elif board_name =="OPEN_BCI":
            #self.params.serial_port = "COM4" #WINDOWS
            self.params.serial_port = "/dev/cu.usbserial-DM00D4TL" #MAC
            #self.params.serial_port = "/dev/ttyUSB0" # Pi or Linux 
            self.board_id = BoardIds.CYTON_BOARD.value
        elif board_name =="MUSE_S":
            parser = argparse.ArgumentParser()
            parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
                                default=0)
            parser.add_argument('--ip-port', type=int, help='ip port', required=False, default=0)
            parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False,
                                default=0)
            parser.add_argument('--ip-address', type=str, help='ip address', required=False, default='')
            parser.add_argument('--serial-port', type=str, help='serial port', required=False, default='')
            parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='')
            parser.add_argument('--other-info', type=str, help='other info', required=False, default='')
            parser.add_argument('--streamer-params', type=str, help='streamer params', required=False, default='')
            parser.add_argument('--serial-number', type=str, help='serial number', required=False, default='MuseS-864C')
            parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards',default=39)
            parser.add_argument('--file', type=str, help='file', required=False, default='')
            args = parser.parse_args()

            self.params.ip_port = args.ip_port
            self.params.serial_port = args.serial_port
            self.params.mac_address = args.mac_address
            self.params.other_info = args.other_info
            self.params.serial_number = args.serial_number
            self.params.ip_address = args.ip_address
            self.params.ip_protocol = args.ip_protocol
            self.params.timeout = args.timeout
            self.params.file = args.file
            self.board_id = args.board_id
        else:
            print("Board ID wrong, using synthetic board")
            self.board_id = BoardIds.SYNTHETIC_BOARD.value

        
        # board_id = BoardIds.SYNTHETIC_BOARD.value
        # board_id = BoardIds.CYTON_BOARD.value

        self.channels = BoardShim.get_eeg_channels(self.board_id)
        if board_name == "MUSE_S":
            #todo: MUSE_S has 4 EEG channels, can be used together to improve accuracy
            self.eeg_channel = self.channels[-1]
            #MUSE_S does not have EOG channel
            self.eog_channel = self.channels[2]
        else:
            self.eeg_channel = self.channels[0]
            print('eeg channel number=', self.channels[0] )
            self.eog_channel = self.channels[2]
            #Rohit's EOG classifier
            self.eog_channel_left = self.channels[2] #left electrode Channel 3
            print('eog channel number=', self.channels[2] )
            self.eog_channel_right = self.channels [1] #right electrode Channel 2
            print('eog channel number=', self.channels[1] )



        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.nfft = DataFilter.get_nearest_power_of_two(self.sampling_rate)
        self.board = BoardShim(self.board_id, self.params)
        self.num_channels = 3
        self.raw_data = []
        self.fil_data = []
        self.person_name = 'Cosmos'
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))
        self.data_folder = os.path.join(self.current_file_path, "cnn eog data", self.person_name)
        self.raw_data_path = os.path.join(self.data_folder, f"{self.person_name}_eog_raw_slow_data.json")
        self.fil_data_path = os.path.join(self.data_folder, f"{self.person_name}_eog_fil_slow_data.json")
        os.makedirs(self.data_folder, exist_ok=True)


        self.timeoutCnt = 0
        self.TIMEOUT_THRESHOLD = 1901 # 1901*0.5 = 950.5 seconds = 15 minutes

        ## Connect to the board and prepare to start streaming data
        while self.board.is_prepared()==False:
                    print("trying to connect to board...")
                    try:
                        self.board.prepare_session()
                        self.board.start_stream()
                        # Graph(board)
                    except:
                        print("reconnection failed. Try again...")
                        time.sleep(1) ## wait for a bit 
        print("reconnection finished")
        

    def update(self):
        while True:
            # while myArgs.isInterrupt==False:
            if self.timeoutCnt>=self.TIMEOUT_THRESHOLD: #the board lost connection or something, restart it
                self.timeoutCnt=0
                print("time up. reconnect...")
                self.board.release_session()
                time.sleep(1) ## wait for a bit 
                while self.board.is_prepared()==False:
                    print("trying to connect to board...")
                    try:
                        self.board.prepare_session()
                        self.board.start_stream()
                        # Graph(board)
                    except:
                        print("reconnection failed. Try again...")
                        time.sleep(1) ## wait for a bit 
                print("reconnection finished")

  
            else: # else, just keep updating eog stuff
                time.sleep(0.5) # controlling timing and initialising variables //////////////
                self.timeoutCnt+=1
                # creating initial dummy data dummy data array for rolling time window and filter size
                if self.timeoutCnt % 4 == 1:
                    label = "Left"
                    print("""
                    _.-"/______________________/////
                    `'-.\~~~~~~~~~~~~~~~~~~~~~~\\\\\
                    """)
                elif self.timeoutCnt % 4 == 2:
                    label = "Neutral"
                    print("""
                       ^
                      ^^^
                     ^^^^^
                    ^^^^^^^      
                    """)
                elif self.timeoutCnt % 4 == 3:
                    label = "Right"
                    print("""
                    \\\\\______________________\`-._
                    /////~~~~~~~~~~~~~~~~~~~~~~/.-'`
                    """)
                else: 
                    label = "Neutral"
                    print("""
                       ^
                      ^^^
                     ^^^^^
                    ^^^^^^^      
                    """)
                # time.sleep(0.5) # compensate for closed eyes test where someone tells you which way to look
                time.sleep(0.3) # for open bci to catch up
                eog_data = self.board.get_board_data(250)
                eog_left_data = eog_data[self.eog_channel_left]
                eog_right_data = eog_data[self.eog_channel_right]
                
                self.raw_data.append({
                    "name": self.person_name,
                    "label": label,
                    "eog_left": eog_left_data.tolist(),
                    "eog_right": eog_right_data.tolist()
                })

                # Save the data to a file
                with open(self.raw_data_path, "w") as f:
                    json.dump(self.raw_data, f)

                DataFilter.detrend(eog_left_data, DetrendOperations.LINEAR.value)
                DataFilter.detrend(eog_right_data, DetrendOperations.LINEAR.value)
                DataFilter.perform_bandpass(eog_left_data, self.sampling_rate, 0.3, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
                DataFilter.perform_bandpass(eog_right_data, self.sampling_rate, 0.3, 6, 4, FilterTypes.BUTTERWORTH.value, 0)

                self.fil_data.append({
                    "name": self.person_name,
                    "label": label,
                    "eog_left": eog_left_data.tolist(),
                    "eog_right": eog_right_data.tolist()  # Convert numpy array to list for JSON serialization
                })

                # Save the data to a file
                with open(self.fil_data_path, "w") as f:
                    json.dump(self.fil_data, f)
                

         
def main():
    
    board = Detector("OPEN_BCI")
    #board = Detector()
    #graph = GraphDrawer.Graph(board_shim=board)
    # graph = None
    board_thread = Thread(target=lambda: board.update())
    board_thread.start()

if __name__ == "__main__":
    main()
