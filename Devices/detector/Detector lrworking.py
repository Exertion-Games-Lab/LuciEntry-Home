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

import os

class Parameter(object):
    pass

# A global variable to store the REM state
rem_state = {}

#command parameters are the wrokaround for us to communicate with the code: CommandSender
def detection(commandParameters=[], board_name = "SYNTHETIC"):
    ## Init board and streaming params 
    params = BrainFlowInputParams()

    # Identify serial port location of Wifi dongle
    # if you are using windows or mac, you will need to change below to your specific serial port directiory
    # if you are using a raspberry pi, it should work without needing to modify it
    # if you are using synthetic data, this dosent matter as it wont get used
    if board_name =="SYNTHETIC":
        # Synthetic for generating fake data, cyton for using the actual real board
        board_id = BoardIds.SYNTHETIC_BOARD.value
    elif board_name =="OPEN_BCI":
        params.serial_port = "COM4" #WINDOWS
        #params.serial_port = "/dev/cu.usbserial-DM00D4TL" #MAC
        # params.serial_port = "/dev/ttyUSB0" # Pi or Linux 
        board_id = BoardIds.CYTON_BOARD.value
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

        params.ip_port = args.ip_port
        params.serial_port = args.serial_port
        params.mac_address = args.mac_address
        params.other_info = args.other_info
        params.serial_number = args.serial_number
        params.ip_address = args.ip_address
        params.ip_protocol = args.ip_protocol
        params.timeout = args.timeout
        params.file = args.file
        board_id = args.board_id
    else:
        print("Board ID wrong, using synthetic board")
        board_id = BoardIds.SYNTHETIC_BOARD.value

    
    # board_id = BoardIds.SYNTHETIC_BOARD.value
    # board_id = BoardIds.CYTON_BOARD.value

    channels = BoardShim.get_eeg_channels(board_id)
    if board_name == "MUSE_S":
        #todo: MUSE_S has 4 EEG channels, can be used together to improve accuracy
        eeg_channel = channels[-1]
        #MUSE_S does not have EOG channel
        eog_channel = channels[2]
    else:
        eeg_channel = channels[0]
        eog_channel = channels[2]
        #Rohit's EOG classifier
        eog_channel_left = channels[2] #left electrode Channel 3
        eog_channel_right = channels [1] #right electrode Channel 2


    sleep_stage = 'Awake'

    sampling_rate = BoardShim.get_sampling_rate(board_id)
    nfft = DataFilter.get_nearest_power_of_two(sampling_rate)
    board = BoardShim(board_id, params)


    # Loading the sleep stageing model from file
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the path to the file you want to load
    sleep_stager_file_path = os.path.join(current_dir, 'SleepStager_bands_SVM.sav')

    ## Initialise the sleep stage classifier 
    sleep_stager = pickle.load(open(sleep_stager_file_path, 'rb'))

    ## Connect to the board and prepare to start streaming data
    board.prepare_session()
    board.start_stream()

    # mean_EOG = 0
    # time_counter = 0

    # LR signal counters
    N_count = 0
    L_count = 0
    LR_count = 0
    T_count = 0

    # yasa counter
    yasa_data = np.ndarray(0)
    
    # participant and save file data
    participant_name = "Cosmos"
    sleep_data_file_name = date.today().strftime("%d_%m_%Y") + '_'+ participant_name + '_log.txt'

    #reconnected counter
    timeoutCnt = 0
    TIMEOUT_THRESHOLD = 1901

    #calculate REM every TIME_WINDOW
    TIME_WINDOW = 120
    #how much percentage can be count as a real REM
    accepted_REM_percentage = 0.6
    #list of sleep stage within last TIME_PERIOD
    sleep_stage_list = ["NaN"]* TIME_WINDOW
    #how many REM are in the list
    REM_cnt = 0
    #final result
    sleep_stage_with_period = "NaN"



    while True:
    # while myArgs.isInterrupt==False:
        
        if timeoutCnt>=TIMEOUT_THRESHOLD: #the board lost connection or something, restart it
            timeoutCnt=0
            print("restart...")
            #release the session first and restart
            if board.is_prepared():
                board.release_session()
            time.sleep(1)
            #restart
            board.prepare_session()
            board.start_stream()


        if board.get_board_data_count() > 8999: #if there is enough samples to calculate sleep stage (3000 samples needed), classify sleep

            # pull new data from the buffer
            eeg_data = board.get_board_data()

            # process data
            # this peforms some denoising to the data and peforms a spectral analysis to get power spectal density (psd)
            DataFilter.perform_downsampling(eeg_data[eeg_channel], 3, AggOperations.MEDIAN.value)
            DataFilter.detrend(eeg_data[eeg_channel], DetrendOperations.LINEAR.value)
            psd = DataFilter.get_psd_welch(eeg_data[eeg_channel], nfft, nfft // 2, sampling_rate,
                                        WindowOperations.BLACKMAN_HARRIS.value)

            # the power of each eeg bandwidth is then extracted from psd and added to an array
            delta = DataFilter.get_band_power(psd, 0.5, 4.0)
            theta = DataFilter.get_band_power(psd, 4.0, 8.0)
            alpha = DataFilter.get_band_power(psd, 8.0, 14.0)
            beta = DataFilter.get_band_power(psd, 14.0, 30.0)
            gamma = DataFilter.get_band_power(psd, 30.0, 45.0)
            bands = np.array([delta, theta, alpha, beta, gamma])
            bands = np.reshape(bands,(1,5))

            # the array is then fit to the model we made earlier to classify sleep stage
            sleep_stage_class = sleep_stager.predict(bands)

            if sleep_stage_class == 0.0:
                sleep_stage = "Awake"
            if sleep_stage_class == 1.0:
                sleep_stage = "NREM"
            if sleep_stage_class == 4.0:
                sleep_stage = "REM"


            





        else: # else, just keep updating eog stuff
            time.sleep(0.2)
            if board.get_board_data_count() < 150:
                continue
            timeoutCnt+=1
            eog_data = board.get_current_board_data(150)
            # Applying filters to channels
            DataFilter.detrend(eog_data[eog_channel_left], DetrendOperations.LINEAR.value)
            DataFilter.detrend(eog_data[eog_channel_right], DetrendOperations.LINEAR.value)
            DataFilter.perform_bandpass(eog_data[eog_channel_left], 150, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandpass(eog_data[eog_channel_right], 150, 0.5, 6, 4, FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_rolling_filter(eog_data[eog_channel_left], 5, AggOperations.MEAN.value)
            DataFilter.perform_rolling_filter(eog_data[eog_channel_right], 5, AggOperations.MEAN.value)
            #labels
            eog_data_filtered_left = eog_data[eog_channel_left]
            eog_data_filtered_right = eog_data[eog_channel_right]
            eog_class_3 = "neutral"

            max_left = np.max(eog_data[eog_channel_left])
            min_left = np.min(eog_data[eog_channel_left])
            max_right = np.max(eog_data[eog_channel_right])
            min_right = np.min(eog_data[eog_channel_right])
            print('max right= ' ,max_right)
            print('max left= ' ,max_left)
            max_left_id = np.argmax(eog_data[eog_channel_left])
            min_left_id = np.argmin(eog_data[eog_channel_left])
            max_right_id = np.argmax(eog_data[eog_channel_right])
            min_right_id = np.argmin(eog_data[eog_channel_right])
            
            if max_right < 500 and max_left < 500:
                if abs(max_right_id - min_left_id) < 10 or abs(max_left_id - min_right_id) < 10:
                    if max_left_id < max_right_id and min_left_id > min_right_id:
                        eog_class_3 = "right"
                    if max_left_id > max_right_id and min_left_id < min_right_id:
                        eog_class_3 = "left"
            print("EOG Class:", eog_class_3)

 # IF statements searching for LR signal
            T_count +=1
            if eog_class_3 == "left":
               L_count = 1
               N_count = 0

            if eog_class_3 == 'neutral':
               N_count += 1

            if L_count == 0 and eog_class_3 == "right":
               N_count += 1

            if N_count == 15 : #error threshold so if there are N_count missed turns it resets:
               L_count = 0

            if L_count == 1 and eog_class_3 == "right":
               LR_count += 1
               L_count = 0

            if LR_count == 4 : # number of LR signals you would like to receive
               print("LR signal received !!!")

            if T_count == 70 : # period of eogclasses we would like to store is counted by the number of main loops that happen
               LR_count = 0
               T_count = 0

            #calculate REM within TIME_PERIOD to make sure user is really in the REM stage
            
            #pop out the first element
            if sleep_stage_list[0] == "REM":
                REM_cnt-=1
            sleep_stage_list.pop(0)
            #add the latest result
            if sleep_stage == "REM":
                REM_cnt+=1
            sleep_stage_list.append(sleep_stage)

            if REM_cnt >= TIME_WINDOW * accepted_REM_percentage:
                sleep_stage_with_period = "REM_PERIOD"
            else:
                sleep_stage_with_period = "Not_REM_PERIOD"




        commandParameters.sleep_stage = sleep_stage_with_period # aaaaaaa
        commandParameters.eog_class = eog_class_3
        t = time.asctime()
        # t = time.localtime()
        # currentTime = time.strftime("%H:%M:%S",t)
        message = t +": "
        if commandParameters.induction==False:
            # message += "sleep stage: "+ sleep_stage + ", EOG Class: "+str(eog_class)+ '\n'   
            message += "sleep stage: "+ sleep_stage + ", Period result: "+ sleep_stage_with_period + '\n'  
             # Store/update REM state in the global variable
            global rem_state
            rem_state = {'state': sleep_stage_with_period}  
        else:
            message += "EOG Class: " + str(eog_class_3) +'\n'   
        f = open(sleep_data_file_name, "a")
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

def main():
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0',port = '5050', debug=True, use_reloader=False))
    flask_thread.start()

    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    commandParameters.induction = False
    detection(commandParameters,board_name = "OPEN_BCI")

if __name__ == "__main__":
    main()
