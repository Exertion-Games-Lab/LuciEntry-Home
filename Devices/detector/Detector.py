import argparse
from datetime import date
import time
import numpy as np 
import pickle

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, WindowOperations, DetrendOperations

import os

class Parameter(object):
    pass

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
        params.serial_port = "COM3" #WINDOWS
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



    # this part sets the baseline for classification of LR signal
    # i dont know why but it works better if you do this twice lol 
    time.sleep(1)
    eog_data = board.get_current_board_data(250)
    DataFilter.detrend(eog_data[eog_channel], DetrendOperations.LINEAR.value)
    eog_baseline_mean = np.mean(eog_data[eog_channel])
    eog_baseline_std = np.std(eog_data[eog_channel])

    time.sleep(1)
    eog_data = board.get_current_board_data(250)
    DataFilter.detrend(eog_data[eog_channel], DetrendOperations.LINEAR.value)
    eog_baseline_mean = np.mean(eog_data[eog_channel])
    eog_baseline_std = np.std(eog_data[eog_channel])


    # mean_EOG = 0
    # time_counter = 0

    participant_name = "Cosmos"
    sleep_data_file_name = date.today().strftime("%d_%m_%Y") + '_'+ participant_name + '_log.txt'

    #reconnected counter
    timeoutCnt = 0
    TIMEOUT_THRESHOLD = 601

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


        if board.get_board_data_count() > 2999: #if there is enough samples to calculate sleep stage (3000 samples needed), classify sleep

            # pull new data from the buffer
            eeg_data = board.get_board_data()

            # process data
            # this peforms some denoising to the data and peforms a spectral analysis to get power spectal density (psd)
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
            time.sleep(1)
            timeoutCnt+=1
            eog_data = board.get_current_board_data(250)
            DataFilter.detrend(eog_data[eog_channel], DetrendOperations.LINEAR.value)

            eog_mean = np.mean(eog_data[eog_channel])

            offset = 0.5
            if eog_mean < eog_baseline_mean + offset and eog_mean > eog_baseline_mean - offset:
                eog_class = "neutral"
            else:
                if eog_mean > eog_baseline_mean:
                    eog_class = "left"
                if eog_mean < eog_baseline_mean:
                    eog_class = "right"


            # eog_data = board.get_current_board_data(250)
            # data = np.array(eog_data[eog_channel_left])
            # DataFilter.detrend(eog_data[eog_channel_left], DetrendOperations.LINEAR.value)
            # DataFilter.detrend(eog_data[eog_channel_right], DetrendOperations.LINEAR.value)
            # mean_value_left = np.mean(eog_data[eog_channel_left])
            # mean_value_right = np.mean(eog_data[eog_channel_right])
            # time_counter += 1

            # LR = 'none'
            # if mean_EOG == 0 or time_counter < 5:
            #     mean_EOG = mean_value_left

            # if time_counter >10:
            #     if mean_value_left < (mean_EOG - 0.5):
            #         LR = "Right"
            #     elif mean_value_left > (mean_EOG + 0.5):
            #         LR = "Left"
            # eog_class = LR



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
                sleep_stage_with_period = "REM_PEROID"
            else:
                sleep_stage_with_period = "Not_REM_PEROID"




        commandParameters.sleep_stage = sleep_stage_with_period
        commandParameters.eog_class = eog_class
        t = time.asctime()
        # t = time.localtime()
        # currentTime = time.strftime("%H:%M:%S",t)
        message = t +": "
        if commandParameters.induction==False:
            # message += "sleep stage: "+ sleep_stage + ", EOG Class: "+str(eog_class)+ '\n'   
            message += "sleep stage: "+ sleep_stage + ", Period result: "+ sleep_stage_with_period + '\n'  
        else:
            message += "EOG Class: " + str(eog_class) +'\n'   
        f = open(sleep_data_file_name, "a")
        f.write(message)
        f.close()
        print(message)

def main():
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    commandParameters.induction = False
    detection(commandParameters,board_name = "OPEN_BCI")

if __name__ == "__main__":
    main()
