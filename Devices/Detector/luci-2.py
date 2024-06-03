import time
import numpy as np 
import pickle

from sklearn.preprocessing import MinMaxScaler
from collections import deque
from statistics import mean

import multiprocessing as mp
from multiprocessing import Process

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, WindowOperations, DetrendOperations

## Init board and streaming params 
params = BrainFlowInputParams()

# Identify serial port location of Wifi dongle
# if you are using windows or mac, you will need to change below to your specific serial port directiory
# if you are using a raspberry pi, it should work without needing to modify it
# if you are using synthetic data, this dosent matter as it wont get used

# params.serial_port = "COM4" #WINDOWS
params.serial_port = "/dev/cu.usbserial-D200RE9I" #MAC 
# params.serial_port = "/dev/ttyUSB0" # Pi or Linux 

""" #Read from file but not working
params.file = "sample.csv" # Read from file
params.master_board = BoardIds.SYNTHETIC_BOARD
"""

# Synthetic for generating fake data, cyton for using the actual real board
#board_id = BoardIds.SYNTHETIC_BOARD.value
board_id = BoardIds.CYTON_BOARD.value

channels = BoardShim.get_eeg_channels(board_id)
eeg_channel = channels[0]
eog_channel_left = channels[2] #left electrode Channel 3
eog_channel_right = channels [1] #right electrode Channel 2

sleep_stage = 'Awake'

sampling_rate = BoardShim.get_sampling_rate(board_id)
nfft = DataFilter.get_nearest_power_of_two(sampling_rate)
board = BoardShim(board_id, params)

""" #When reading from file but not working
board = BoardShim(BoardIds.PLAYBACK_FILE_BOARD, params) #For reading from file
"""
## Initialise the sleep stage classifier 
sleep_stager = pickle.load(open('SleepStager_bands_SVM.sav', 'rb'))


## Connect to the board and prepare to start streaming data
board.prepare_session()
board.start_stream()

"""
mean_ten = deque([0], maxlen=5) #stores last 10 seconds of mean EOG values
mean_two = deque([0,0], maxlen=2) #stores last 2 seconds of mean EOG values
"""
mean_EOG = 0


time_counter = 0

while True:

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
        eog_data = board.get_current_board_data(250)
        data = np.array(eog_data[eog_channel_left])
        DataFilter.detrend(eog_data[eog_channel_left], DetrendOperations.LINEAR.value)
        DataFilter.detrend(eog_data[eog_channel_right], DetrendOperations.LINEAR.value)
        mean_value_left = np.mean(eog_data[eog_channel_left])
        mean_value_right = np.mean(eog_data[eog_channel_right])
        time_counter += 1

        LR = 'none'
        
        # LR Detection #
        # Algorithm works by comparing the last two seconds of sample data with the average of over 10 seconds of EOG data. If the EOG value increases by 60% in the first second then decreases
        # by 60% in the 2nd second then it is a left eye movement and vise versa. Assumptions for now is it will only work over 2 seconds periods of far left/right to middle where one second
        # is dedicated for each movement. Allow first 10 seconds to accumalate before accurate(ish?) reading.
        
        
        """ mean_two.append(mean_value) #append mean value of current sample to mean_two which we will use to analyse eye movement over a 2 second span
        
        if (mean_two[0] > (mean(mean_ten)+0.6*mean(mean_ten))) and (mean_two[1] < (mean(mean_ten)-0.6*mean(mean_ten))): #if EOG goes up and down we have left eye movement (60% threshhold)
            LR = "left"
        elif (mean_two[0] < (mean(mean_ten)-0.6*mean(mean_ten))) and (mean_two[1] > (mean(mean_ten)+0.6*mean(mean_ten))): #if EOG goes down then up we have right eye movement (60% threshold)
            LR = "right"
        else:
            LR = "none"
            mean_ten.append(mean_value) #append mean value of current sample to mean_ten which we will use to determine what the EOG value will look like when no movement in eyes
        """
        if mean_EOG == 0 or time_counter < 5:
            mean_EOG = mean_value_left

        if time_counter >10:
            if mean_value_left < (mean_EOG - 0.5):
                LR = "Right"
            elif mean_value_left > (mean_EOG + 0.5):
                LR = "Left"

        
        #Debug section (Uncomment for more raw input prints)
        print(mean_EOG, time_counter)
        #detect_right_left(data)
        #print(data)
        #print('Mean of last 10: '+ str(mean(mean_ten)) + " Mean of last 2: "+ str(mean(mean_two))) 

    print("sleep stage: "+ sleep_stage + ", EOG Value(Left, Right): " + str(mean_value_left) +" , "+ str(mean_value_right) + " LR: " + LR)
    


        