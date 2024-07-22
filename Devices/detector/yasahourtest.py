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
            self.params.serial_port = "COM4" #WINDOWS
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
        self.Yasa_sleep_stage = 'Awake'
        self.Yasa_hour_sleep_stage = 'Awake'

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
        self.sleep_stage_array = np.empty(2, dtype=object)
        self.started_staging = 0
        self.message_truth = 0
        self.time_length = 0
        self.yasa_filename = date.today().strftime("%d_%m_%Y") + '_EEG-log'
        
        # participant and save file data
        participant_name = "Cosmos"
        self.sleep_data_file_name = date.today().strftime("%d_%m_%Y") + '_' + participant_name + '_log.txt'

        #reconnected counter
        self.timeoutCnt = 0
        self.TIMEOUT_THRESHOLD = 1901

        #calculate REM every TIME_WINDOW
        self.TIME_WINDOW = 120
        #how much percentage can be count as a real REM
        self.accepted_REM_percentage = 0.6
        #list of sleep stage within last TIME_PERIOD
        self.sleep_stage_list = ["NaN"]* self.TIME_WINDOW
        self.Yasa_sleep_stage_list = ["NaN"]* self.TIME_WINDOW
        self.Yasa_hour_sleep_stage_list = ["NaN"]* self.TIME_WINDOW

        #how many REM are in the list
        self.REM_cnt = 0
        self.Yasa_REM_cnt = 0
        self.Yasa_hour_REM_cnt = 0
        #final result
        self.sleep_stage_with_period = "NaN"
        self.Yasa_sleep_stage_with_period = "NaN"
        self.Yasa_hour_sleep_stage_with_period = "NaN"

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
                self.message_truth = 1
                # pull new data from the buffer
                self.eeg_data = self.board.get_board_data()
                DataFilter.detrend(self.eeg_data[self.eeg_channel], DetrendOperations.LINEAR.value)
                DataFilter.detrend(self.eeg_data[self.eog_channel_right], DetrendOperations.LINEAR.value)
                
                # yasa_hour_data_comb1 = np.vstack((self.eeg_data[self.eeg_channel] , self.eeg_data[self.eog_channel_left]))
                # add it to the file
                if self.started_staging == 1: # with current structure open bci needs to reset before an hours dat is collected so it is wiped
                    # data = np.load(self.yasa_filename +'.npy')
                    # print('data shape =', np.shape(data))
                    # yasa_hour_eog = data[0,:].tolist()
                    # print('data list =', np.shape(data))
                    # yasa_hour_eog.extend(self.eeg_data[self.eeg_channel])  # Append elements
                    # print('extended data shape =', np.shape(yasa_hour_eog))
                    # yasa_eog_array= np.array(yasa_hour_eog)
                    # print('array shape =', np.shape(yasa_eog_array))

                    # yasa_hour_eeg = data[1,:].tolist() 
                    # yasa_hour_eeg.extend(self.eeg_data[self.eog_channel_left])  # Append elements
                    # yasa_eeg_array= np.array(yasa_hour_eeg)
                    # print("eog_array:",np.shape(yasa_eog_array))
                    
                    # yasa_hour_data_comb = np.vstack((yasa_eog_array , yasa_eeg_array))

                    # print('yasa_night_length',np.shape(yasa_hour_data_comb))

                    # np.save(self.yasa_filename, yasa_hour_data_comb)

                    self.sleep_stage_array[0] = np.concatenate((self.sleep_stage_array[0], self.eeg_data[self.eeg_channel]))
                    self.sleep_stage_array[1] = np.concatenate((self.sleep_stage_array[1], self.eeg_data[self.eog_channel_right]))
                    print("sleep stage extended",np.shape(self.sleep_stage_array))
                    print('eeg length', len(self.sleep_stage_array[0]))
                    print('eog length', len(self.sleep_stage_array[1]))
                    

                else:
                    # yasa_hour_data_comb = np.vstack((self.eeg_data[self.eeg_channel] , self.eeg_data[self.eog_channel_left]))
                    # print('yasa_night_length start',np.shape(yasa_hour_data_comb))
                    
                    # np.save(self.yasa_filename, yasa_hour_data_comb)

                    self.sleep_stage_array[0] = self.eeg_data[self.eeg_channel]
                    self.sleep_stage_array[1] = self.eeg_data[self.eog_channel_right]
                    print('eeg length', len(self.sleep_stage_array[0]))
                    print('eog length', len(self.sleep_stage_array[1]))
                
                    print('yasa_array_test',len(self.sleep_stage_array[0]))
                    self.started_staging = 1
                self.time_length = (len(self.sleep_stage_array[0]))


            # processing yasa model


                print("yasa length:",len(self.sleep_stage_array[0]))
                if len(self.sleep_stage_array[0]) > 90000: #(storage arrays need to be wiped each five mins)
                    print("length enough 1 ")
                    info = create_info(ch_names=["EEG","EOG"],sfreq = self.sampling_rate, ch_types = ["eeg","eog"])

                    array_for_yasa = np.vstack((self.sleep_stage_array[0],self.sleep_stage_array[1]))
                    print('array shape', np.shape(array_for_yasa))
                    array_for_yasa.reshape(2,-1)
                    raw = RawArray(array_for_yasa, info)
                    Yasa_hour_stages = yasa.SleepStaging(raw , eeg_name='EEG', eog_name='EOG').predict()
                    print("yasa stage:",Yasa_hour_stages)
                    # at a count of 90000 samples sleep stager prints yasa stage: ['W' 'W' 'W' 'W' 'W' 'W' 'W' 'W' 'N1' 'N1' 'N1' 'N1']
                    last_hour = len(Yasa_hour_stages) -1
                    # print("last sleep stage:", Yasa_stages[last])

                    if Yasa_hour_stages[last_hour] == 'W':
                        self.Yasa_hour_sleep_stage = 'Awake'
                    if Yasa_hour_stages[last_hour] == 'N1' or Yasa_hour_stages[last_hour] == 'N2' or Yasa_hour_stages[last_hour] == 'N3':
                        self.Yasa_hour_sleep_stage = "NREM"
                    if Yasa_hour_stages[last_hour] == 'R':
                        self.Yasa_hour_sleep_stage = "REM"
                    # print("Yasa sleep stage: " , Yasa_sleep_stage)
                    
                    # Yasa_hour_stages_without = yasa.SleepStaging(raw , eeg_name='EEG').predict()
                    # if Yasa_hour_stages_without[last_hour] == 'W':
                    #     self.Yasa_sleep_stage = 'Awake'
                    # if Yasa_hour_stages_without[last_hour] == 'N1' or Yasa_hour_stages[last_hour] == 'N2' or Yasa_hour_stages[last_hour] == 'N3':
                    #     self.Yasa_sleep_stage = "NREM"
                    # if Yasa_hour_stages_without[last_hour] == 'R':
                    #     self.Yasa_sleep_stage = "REM"


                
                #calculate REM within TIME_PERIOD to make sure user is really in the REM stage

            #yasa hour model
            #pop out the first element
            if self.Yasa_hour_sleep_stage_list[0] == "REM":
                self.Yasa_hour_REM_cnt-=1
            self.Yasa_hour_sleep_stage_list.pop(0)
            #add the latest result
            if self.Yasa_hour_sleep_stage == "REM":
                self.Yasa_hour_REM_cnt+=1
            self.Yasa_hour_sleep_stage_list.append(self.Yasa_hour_sleep_stage)

            if self.Yasa_hour_REM_cnt >= self.TIME_WINDOW * self.accepted_REM_percentage:
                self.Yasa_hour_sleep_stage_with_period = "REM_PEROID"
            else:
                self.Yasa_hour_sleep_stage_with_period = "Not_REM_PEROID"





            # self.commandParameters.sleep_stage = self.sleep_stage_with_period
            # self.commandParameters.eog_class = eog_class
            t = time.asctime()
            # t = time.localtime()
            # currentTime = time.strftime("%H:%M:%S",t)
            message = t +": "
            # if self.commandParameters.induction==False:
            # message += "sleep stage: "+ sleep_stage + ", EOG Class: "+str(eog_class)+ '\n'   
            message += ", Yasa hour sleep stage: " + self.Yasa_hour_sleep_stage + ", Yasa hour Sleep Period: "+ self.Yasa_hour_sleep_stage_with_period 
            message += ", Yasa hour sleep stage without: " + self.Yasa_sleep_stage + ", time window length:" + str(self.time_length) + '\n'

            # Store/update REM state in the global variable
            global rem_state
            rem_state = {'state': self.Yasa_hour_sleep_stage_with_period}  
            #rem_state = {'state': self.sleep_stage_with_period} 
            # else:
            #     message += "EOG Class: " + str(eog_class) +'\n' 
            if self.message_truth == 1 :
                f = open(self.sleep_data_file_name, "a")
                f.write(message)
                f.close()
                print(message)

            self.message_truth = 0



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
