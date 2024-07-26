import argparse
from datetime import date
import time
import numpy as np 
import pickle
import time
import yasa
from mne import create_info
from mne.io import RawArray
from flask import Flask, jsonify, request
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
            self.params.serial_port = "COM3" #WINDOWS
            #params.serial_port = "/dev/cu.usbserial-DM00D4TL" #MAC
            # self.params.serial_port = "/dev/ttyUSB0" # Pi or Linux 
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
            print('eeg channel nuber=', self.channels[0] )
            self.eog_channel = self.channels[2]
            #Rohit's EOG classifier
            self.eog_channel_left = self.channels[2] #left electrode Channel 3
            print('eog channel nuber=', self.channels[2] )
            self.eog_channel_right = self.channels [1] #right electrode Channel 2
            print('eog channel nuber=', self.channels[1] )


        self.sleep_stage = 'Awake'

        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.nfft = DataFilter.get_nearest_power_of_two(self.sampling_rate)
        self.board = BoardShim(self.board_id, self.params)
        self.num_channels = 3

        # Loading the sleep stageing model from file
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the file you want to load
        sleep_stager_file_path = os.path.join(current_dir, 'SleepStager_bands_SVM.sav')

        ## Initialise the sleep stage classifier 
        self.sleep_stager = pickle.load(open(sleep_stager_file_path, 'rb'))

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
        # In your main detection function
        # app = QtWidgets.QApplication([])
        # eog_graph = EogGraph()
        # eog_graph.show()
        # mean_EOG = 0
        # time_counter = 0
        self.eeg_data = np.ndarray(0)
        self.eog_class = "neutral"
        # LR signal counters
        self.N_count = 0
        self.L_count = 0
        self.LR_count = 0
        self.T_count = 0
        self.LR_count_perm = 0
        

        # yasa counter
        self.sleep_stage_array = np.ndarray(0)
        self.stager_info = create_info(ch_names=["EEG"],sfreq = self.sampling_rate, ch_types = ["eeg"])
        self.started_staging = 0
        self.yasa_filename = date.today().strftime("%d_%m_%Y") + '_EEG-log'
        
        # participant and save file data
        participant_name = "Cosmos"
        self.sleep_data_file_name = date.today().strftime("%d_%m_%Y") + '_' + participant_name + '_log.txt'

        #reconnected counter
        self.timeoutCnt = 0
        self.TIMEOUT_THRESHOLD = 100

        #calculate REM every TIME_WINDOW
        self.TIME_WINDOW = 120
        #how much percentage can be count as a real REM
        self.accepted_REM_percentage = 0.6
        #list of sleep stage within last TIME_PERIOD
        self.sleep_stage_list = ["NaN"]* self.TIME_WINDOW

        #how many REM are in the list
        self.REM_cnt = 0
        #final result
        self.sleep_stage_with_period = "NaN"

    def update(self, graph):
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

            
                # #release the session first and restart
                # if board.is_prepared():
                #     board.release_session()
                # time.sleep(1)
                # #restart
                # board.prepare_session()
                # board.start_stream()


            if self.board.get_board_data_count() > 8999: #if there is enough samples to calculate sleep stage (3000 samples needed), classify sleep

                # pull new data from the buffer
                self.eeg_data = self.board.get_board_data()
                DataFilter.detrend(self.eeg_data[self.eeg_channel], DetrendOperations.LINEAR.value)
                # DataFilter.detrend(self.eeg_data[self.eog_channel_right], DetrendOperations.LINEAR.value)
                if self.started_staging == 1:
                    self.sleep_stage_array = np.concatenate((self.sleep_stage_array, self.eeg_data[self.eeg_channel]))
                    # self.sleep_stage_array[1] = np.concatenate((self.sleep_stage_array[1], self.eeg_data[self.eog_channel_right]))
                    print("sleep stage extended",np.shape(self.sleep_stage_array))
                else:

                    self.sleep_stage_array = self.eeg_data[self.eeg_channel]
                    # self.sleep_stage_array[1] = self.eeg_data[self.eog_channel_right]
                    # print('eeg length', len(self.sleep_stage_array[0]))
                    # print('eog length', len(self.sleep_stage_array[1]))
                
                    print('yasa_array_test',len(self.sleep_stage_array))
                    self.started_staging = 1
                if len(self.sleep_stage_array) > 90000: #(storage arrays need to be wiped each five mins)

                    raw = RawArray((self.sleep_stage_array.reshape(1,-1)), self.stager_info) #might need to reshape .reshape(1,-1)
                    Yasa_hour_stages = yasa.SleepStaging(raw , eeg_name='EEG').predict()
                    print("yasa stage:",Yasa_hour_stages)
                    # at a count of 90000 samples sleep stager prints yasa stage: ['W' 'W' 'W' 'W' 'W' 'W' 'W' 'W' 'N1' 'N1' 'N1' 'N1']
                    last_hour = len(Yasa_hour_stages) -1
                    # print("last sleep stage:", Yasa_stages[last])

                    if Yasa_hour_stages[last_hour] == 'W':
                        self.sleep_stage = 'Awake'
                    if Yasa_hour_stages[last_hour] == 'N1' or Yasa_hour_stages[last_hour] == 'N2' or Yasa_hour_stages[last_hour] == 'N3':
                        self.sleep_stage = "NREM"
                    if Yasa_hour_stages[last_hour] == 'R':
                        self.sleep_stage = "REM"

                
            else: # else, just keep updating eog stuff
                time.sleep(0.2) # controlling timing and initialising variables //////////////
                if self.board.get_board_data_count() < 250 :
                    time.sleep(0.2)
                    # if len(self.eeg_data) > 10: #compensation when the openbci reaches it capture limit and resets
                    #     # print('eeg length', len(self.eeg_data))
                    #     len_test = len(self.eeg_data[self.eeg_channel]) - 2750
                    #     dummy_left = self.eeg_data[self.eog_channel_left]
                    #     dummy_left= dummy_left[len_test:]
                    #     dummy_right = self.eeg_data[self.eog_channel_right]
                    #     dummy_right= dummy_right[len_test:]
                    #     # print('dummy length', len(dummy_left))
                    # else : # just starting 
                    continue
                self.timeoutCnt+=1
                eog_data = self.board.get_current_board_data(250)
                
                # if len(self.eeg_data) > 10:
                #     eog_data_yasa_L = np.concatenate((dummy_left, eog_data[self.eog_channel_left]))
                #     eog_data_yasa_R = np.concatenate((dummy_right, eog_data[self.eog_channel_right]))
                #     yasa_eog_comb = np.vstack((eog_data_yasa_L,eog_data_yasa_R))
                #     yasa_eog_comb = yasa_eog_comb.reshape(2,-1)
                # else :
                #     eog_data_yasa = self.board.get_current_board_data(3000)
                #     yasa_eog_comb = np.vstack((eog_data_yasa[self.eog_channel_left],eog_data_yasa[self.eog_channel_right]))
                #     yasa_eog_comb = yasa_eog_comb.reshape(2,-1)

                # Applying filters to channels
                DataFilter.detrend(eog_data[self.eog_channel_left], DetrendOperations.LINEAR.value)
                DataFilter.detrend(eog_data[self.eog_channel_right], DetrendOperations.LINEAR.value)
                DataFilter.perform_bandpass(eog_data[self.eog_channel_left], 150, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
                DataFilter.perform_bandpass(eog_data[self.eog_channel_right], 150, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
                DataFilter.perform_rolling_filter(eog_data[self.eog_channel_left], 5, AggOperations.MEAN.value)
                DataFilter.perform_rolling_filter(eog_data[self.eog_channel_right], 5, AggOperations.MEAN.value)
                
                
                #graph labels 
                # eog_data_filtered_left = eog_data[self.eog_channel_left]
                # eog_data_filtered_right = eog_data[self.eog_channel_right]
                # eog_graph.eog_data_left = eog_data_filtered_left
                # eog_graph.eog_data_right = eog_data_filtered_right
                # eog_graph.update_graph(eog_data_filtered_left, eog_data_filtered_right)
                eog_data = eog_data[1:,:]
                print(eog_data.shape)
                #graph.setData(eog_data)

                
                eog_class = "neutral"

                max_left = np.max(eog_data[self.eog_channel_left])
                max_right = np.max(eog_data[self.eog_channel_right])
                max_left_id = np.argmax(eog_data[self.eog_channel_left])
                min_left_id = np.argmin(eog_data[self.eog_channel_left])
                max_right_id = np.argmax(eog_data[self.eog_channel_right])
                min_right_id = np.argmin(eog_data[self.eog_channel_right])
                
                if max_right < 500 and max_left < 500:
                    if abs(max_right_id - min_left_id) < 20 or abs(max_left_id - min_right_id) < 20:
                        if max_left_id < max_right_id and min_left_id > min_right_id:
                            eog_class = "right"
                        if max_left_id > max_right_id and min_left_id < min_right_id:
                            eog_class = "left"

                print("EOG Class:", eog_class)

                    #////////////////////////////////////////////////////////////////////////////////////////////////
                #yasa rem_dectect

                # eog_class2 = "neutral"
                
                # DataFilter.detrend(eog_data_yasa[self.eog_channel_left], DetrendOperations.LINEAR.value)
                # DataFilter.detrend(eog_data_yasa[self.eog_channel_right], DetrendOperations.LINEAR.value)
                # DataFilter.perform_bandpass(eog_data_yasa[self.eog_channel_left], self.sampling_rate, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
                # DataFilter.perform_bandpass(eog_data_yasa[self.eog_channel_right], self.sampling_rate, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
                # DataFilter.perform_rolling_filter(eog_data_yasa[self.eog_channel_left], 5, AggOperations.MEDIAN.value)
                # DataFilter.perform_rolling_filter(eog_data_yasa[self.eog_channel_right], 5, AggOperations.MEDIAN.value)

                # yasa_eog_comb = np.vstack((eog_data_yasa[self.eog_channel_left],eog_data_yasa[self.eog_channel_right]))
                # yasa_eog_comb = yasa_eog_comb.reshape(2,-1)
                # try:
                #     rem = yasa.rem_detect(yasa_eog_comb[0,:],yasa_eog_comb[1,:],self.sampling_rate)
                #     # rem = yasa.rem_detect(yasa_eog_comb[0,:],yasa_eog_comb[1,:],
                #     #                        sampling_rate, hypno=None, include=4, amplitude = (50,325),
                #     #                        duration=(0.3,1.5),freq_rem=(0.5,5), remove_outliers=False, verbose=False) 
                #     print("rem_yasa", rem)
                #     mask = rem.get_mask()
                #     loc = (eog_data_yasa[self.eog_channel_left] * mask[0,:])
                #     roc = (eog_data_yasa[self.eog_channel_right] * mask[1,:])
                #     loc = loc[1500:] #(1700-1450=250 values)
                #     roc = roc[1500:]

                #     max_left = np.max(loc)
                #     min_left = np.min(loc)
                #     max_right = np.max(roc)
                #     min_right = np.min(roc)
                #     # print("max right  =",max_right)
                #     # print("max left  =",max_left)
                #     # print("min right  =",min_right)
                #     # print("min left  =",min_left)
                #     max_left_id = np.argmax(loc)
                #     min_left_id = np.argmin(loc)
                #     max_right_id = np.argmax(roc)
                #     min_right_id = np.argmin(roc)
                #     if max_right < 500 and max_left < 500: # to filter out massive spikes caused by noise
                #         if max_right > 1 and max_left > 1: # in genral when left it seems right max is bigger thelaft min
                #             if abs(max_right_id - min_left_id) < 15 or abs(max_left_id - min_right_id) < 15: #matches maxes and mins of the waves
                #                 # if max_left_id < min_left_id and max_right_id > min_right_id:
                #                 if max_left_id < max_right_id and min_left_id > min_right_id:
                #                     eog_class2 = "right" 
                #                     if eog_i_1 == "left" :
                #                         eog_class2 = "neutral"
                #                 # if max_left_id > min_left_id and max_right_id < min_right_id:
                #                 if max_left_id > max_right_id and min_left_id < min_right_id:
                #                     eog_class2 = "left" 
                #                     if eog_i_1 == "right" :
                #                         eog_class2 = "neutral"
                #     print("EOG Class2 passed:", eog_class2)
                # except BaseException:  # in case Yasa Rem_detect triggers an invalididation and reuterns a NONE result
                #     eog_class2 = "neutral"
                #     print("EOG Class2 failed :", eog_class2)
                # eog_i_1 = eog_class2
                # eog_class = eog_class2
                #IF statements searching for LR signal
                self.T_count +=1
                if eog_class == "left":
                    self.L_count = 1
                    self.N_count = 0
                if eog_class == "neutral":
                    self.N_count += 1
                if self.L_count == 0 and eog_class == "right":
                    self.N_count += 1
                if self.N_count == 15: #error threshold so if there are 3 missed turns it resets
                    self.L_count = 0

                if self.L_count == 1 and eog_class == "right":
                    self.LR_count += 1
                    self.L_count = 0
                if self.LR_count == 4: # number of LR signals you would like to receive
                    print("LR signal received !!!") #turn into confirmation signal later
                    self.LR_count_perm += 1
                    self.LR_count = 0
                    # put global variable saying LR signal confirmed
                if self.T_count == 100: # period of eogclasses we would like to store
                    self.LR_count = 0
                    self.T_count = 0

                
                
                
                
                #calculate REM within TIME_PERIOD to make sure user is really in the REM stage
                #nathan's model
                #pop out the first element
            if self.sleep_stage_list[0] == "REM":
                self.REM_cnt-=1
            self.sleep_stage_list.pop(0)
                #add the latest result
            if self.sleep_stage == "REM":
                self.REM_cnt+=1
            self.sleep_stage_list.append(self.sleep_stage)

            if self.REM_cnt >= self.TIME_WINDOW * self.accepted_REM_percentage:
                self.sleep_stage_with_period = "REM_PERIOD"
            else:
                self.sleep_stage_with_period = "Not_REM_PERIOD"


            # self.commandParameters.sleep_stage = self.sleep_stage_with_period
            # self.commandParameters.eog_class = eog_class
            t = time.asctime()
            # t = time.localtime()
            # currentTime = time.strftime("%H:%M:%S",t)
            message = t +": "
            # if self.commandParameters.induction==False:
            # message += "sleep stage: "+ sleep_stage + ", EOG Class: "+str(eog_class)+ '\n'   
            message += "yasa model sleep stage: "+ self.sleep_stage + ", yasa model sleep Period: "+ self.sleep_stage_with_period 
            message += ", LR signal count: " + str(self.LR_count_perm)  + '\n'
            # Store/update REM state in the global variable
            global rem_state
            rem_state = {'state': self.sleep_stage_with_period}  
            #rem_state = {'state': self.sleep_stage_with_period} 
            # else:
            #     message += "EOG Class: " + str(eog_class) +'\n'   
            f = open(self.sleep_data_file_name, "a")
            f.write(message)
            f.close()
            print(message)  



# Flask app setup
app = Flask(__name__)

@app.route('/update_rem', methods=['POST'])
def update_rem():
    global rem_state
    rem_state = request.json
    return jsonify({"message": "REM state updated"}), 200

@app.route('/get_rem', methods=['GET'])
def get_rem():
    return jsonify(rem_state), 200

#we only draw the first 3 EEG for debugging
# EEG_data_queue = GraphDrawer.EEGDataQueue(3)

def main():
    
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0',port = '5050', debug=True, use_reloader=False))
    flask_thread.start()
    board = Detector("OPEN_BCI")
    #board = Detector()
    #graph = GraphDrawer.Graph(board_shim=board)
    graph = None
    board_thread = Thread(target=lambda: board.update(graph))
    board_thread.start()
    
    #graph.update_loop()


    # commandParameters = Parameter()
    # commandParameters.isInterrupt = False
    # commandParameters.induction = False
    # detection(commandParameters,board_name = "SYNTHETIC")

if __name__ == "__main__":
    main()
