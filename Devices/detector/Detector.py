import time
import numpy as np 
import pickle

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, WindowOperations, DetrendOperations

class Parameter(object):
    pass

#command parameters are the wrokaround for us to communicate with the code: CommandSender
def detection(commandParameters=[],isSynthetic = False):
    ## Init board and streaming params 
    params = BrainFlowInputParams()

    # Identify serial port location of Wifi dongle
    # if you are using windows or mac, you will need to change below to your specific serial port directiory
    # if you are using a raspberry pi, it should work without needing to modify it
    # if you are using synthetic data, this dosent matter as it wont get used
    if isSynthetic:
        # Synthetic for generating fake data, cyton for using the actual real board
        board_id = BoardIds.SYNTHETIC_BOARD.value
    else:
        params.serial_port = "COM3" #WINDOWS
        #params.serial_port = "/dev/cu.usbserial-DM00D4TL" #MAC
        # params.serial_port = "/dev/ttyUSB0" # Pi or Linux 
        board_id = BoardIds.CYTON_BOARD.value

    
    # board_id = BoardIds.SYNTHETIC_BOARD.value
    # board_id = BoardIds.CYTON_BOARD.value

    channels = BoardShim.get_eeg_channels(board_id)
    eeg_channel = channels[0]
    eog_channel = channels[2]

    sleep_stage = 'Awake'

    sampling_rate = BoardShim.get_sampling_rate(board_id)
    nfft = DataFilter.get_nearest_power_of_two(sampling_rate)
    board = BoardShim(board_id, params)

    ## Initialise the sleep stage classifier 
    sleep_stager = pickle.load(open('SleepStager_bands_SVM.sav', 'rb'))


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
    while True:
    # while myArgs.isInterrupt==False:

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


        commandParameters.sleep_stage = sleep_stage
        commandParameters.eog_class = eog_class
        t = time.asctime()
        # t = time.localtime()
        # currentTime = time.strftime("%H:%M:%S",t)
        message = t +": "
        if commandParameters.induction==False:
            message += "sleep stage: "+ sleep_stage + ", EOG Class: "+str(eog_class)+ '\n'    
        else:
            message += "EOG Class: " + str(eog_class) +'\n'
        today = "28_09_2023"    
        f = open("cosmos_"+today+" .txt", "a")
        f.write(message)
        f.close()
        print(message)

def main():
    commandParameters = Parameter()
    commandParameters.isInterrupt = False
    commandParameters.induction = False
    detection(commandParameters)

if __name__ == "__main__":
    main()
