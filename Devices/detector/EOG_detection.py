import numpy as np
import time
import pickle
from datetime import datetime
import yasa
from mne import create_info
from mne.io import RawArray
from flask import Flask, jsonify, request
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, DetrendOperations, FilterTypes, AggOperations, WindowOperations
from threading import Thread
import os

# Flask app setup
app = Flask(__name__)

# Global variable to store REM state
rem_state = {}

# Parameters for REM calculation and EOG detection
TIME_WINDOW = 120  # Time window to calculate REM
ACCEPTED_REM_PERCENTAGE = 0.6  # Threshold to count REM
AMPLITUDE_HIGH_THRESHOLD = 80  # High threshold for eye movement detection
AMPLITUDE_LOW_THRESHOLD = 10   # Low threshold for noise filtering
AMPLITUDE_RESET_THRESHOLD = 5  # Threshold to reset after a movement
TIMER_THRESHOLD = 250  # Timer for eye movement state
sampling_rate = 250  # Adjust based on board setup

# Function to classify amplitude levels based on thresholds
def classify_amplitude(value):
    if value >= AMPLITUDE_HIGH_THRESHOLD:
        return "High"
    else:
        return "Low"

# Function to calculate the derivative of the signal
def calculate_derivative(current, previous, n=1):
    return (current - previous) / n

class EOGDetector:
    def __init__(self, board_name="OPEN_BCI"):
        self.state = "INITIAL"
        self.eye_direction = "Neutral"
        self.sleep_stage = "Awake"
        self.sleep_stage_list = ["NaN"] * TIME_WINDOW  # Store sleep stages over a time window
        self.REM_cnt = 0  # REM counter
        self.LR_count_perm = 0

        # BrainFlow Setup
        self.params = BrainFlowInputParams()
        self.params.serial_port = "COM3"  # Modify based on your system setup
        self.board_id = BoardIds.CYTON_BOARD.value
        self.board = BoardShim(self.board_id, self.params)
        self.eeg_channel = BoardShim.get_eeg_channels(self.board_id)[0]
        self.eog_channel_left = BoardShim.get_eeg_channels(self.board_id)[2]
        self.eog_channel_right = BoardShim.get_eeg_channels(self.board_id)[1]

        # Sleep staging model (SVM-based)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, 'SleepStager_bands_SVM.sav')
        self.sleep_stager = pickle.load(open(model_path, 'rb'))

        # Prepare session
        self.board.prepare_session()
        self.board.start_stream()

        # State variables for movement detection
        self.previous_left_signal = 0
        self.previous_right_signal = 0

    def preprocess_signal(self, signal):
        """
        Preprocess EOG signal using bandpass and rolling average filters.
        """
        DataFilter.detrend(signal, DetrendOperations.LINEAR.value)
        DataFilter.perform_bandpass(signal, sampling_rate, 0.1, 30.0, 4, FilterTypes.BUTTERWORTH.value, 0)
        DataFilter.perform_rolling_filter(signal, 3, AggOperations.MEAN.value)
        return signal

    def read_eog_signal(self):
        """
        Get EOG signals from both left and right channels.
        """
        data = self.board.get_current_board_data(150)
        if data.size == 0:
            print("Error: No data retrieved from the board.")
            return None, None

        # Preprocess EOG signals
        left_signal = self.preprocess_signal(data[self.eog_channel_left])
        right_signal = self.preprocess_signal(data[self.eog_channel_right])

        return left_signal, right_signal

    def detect_eye_direction(self, left_eog, right_eog):
        """
        Detect eye movement direction using signal amplitude and derivative (slope).
        Incorporates stages like InitialEdge and FinalEdge detection based on threshold crossing.
        """
        max_left = np.max(left_eog)
        max_right = np.max(right_eog)

        # Derivative calculation (slope)
        derivative_left = calculate_derivative(max_left, self.previous_left_signal)
        derivative_right = calculate_derivative(max_right, self.previous_right_signal)

        # Classify the amplitude levels using thresholds
        left_classification = classify_amplitude(max_left)
        right_classification = classify_amplitude(max_right)

        # Detect eye movement direction based on threshold crossing and derivative
        if left_classification == "High" and derivative_left > AMPLITUDE_LOW_THRESHOLD:
            self.eye_direction = "Left"
            self.state = "InitialEdge+"  # Detected initial edge for left eye movement
        elif right_classification == "High" and derivative_right > AMPLITUDE_LOW_THRESHOLD:
            self.eye_direction = "Right"
            self.state = "InitialEdge+"  # Detected initial edge for right eye movement
        elif abs(derivative_left) < AMPLITUDE_RESET_THRESHOLD and abs(derivative_right) < AMPLITUDE_RESET_THRESHOLD:
            self.eye_direction = "Neutral"
            self.state = "FinalEdge"  # Detected final edge (return to neutral)

        # Store previous signal values for the next iteration
        self.previous_left_signal = max_left
        self.previous_right_signal = max_right

    def process_eeg_data(self, eeg_data):
        """
        Process EEG data for sleep staging (using SVM model) and calculate sleep stage.
        """
        # Ensure EEG data is 1D
        eeg_data = np.squeeze(eeg_data[self.eeg_channel, :])

        # Downsample EEG data
        DataFilter.perform_downsampling(eeg_data, 3, AggOperations.MEDIAN.value)

        # Power Spectral Density (PSD) calculation
        psd = DataFilter.get_psd_welch(eeg_data, 512, 256, self.sampling_rate, WindowOperations.BLACKMAN_HARRIS.value)

        # Extract EEG bands
        delta = DataFilter.get_band_power(psd, 0.5, 4.0)
        theta = DataFilter.get_band_power(psd, 4.0, 8.0)
        alpha = DataFilter.get_band_power(psd, 8.0, 14.0)
        beta = DataFilter.get_band_power(psd, 14.0, 30.0)
        gamma = DataFilter.get_band_power(psd, 30.0, 45.0)
        bands = np.array([delta, theta, alpha, beta, gamma]).reshape(1, -1)

        # Predict sleep stage using SVM model
        sleep_stage_class = self.sleep_stager.predict(bands)[0]
        if sleep_stage_class == 0.0:
            self.sleep_stage = "Awake"
        elif sleep_stage_class == 1.0:
            self.sleep_stage = "NREM"
        elif sleep_stage_class == 4.0:
            self.sleep_stage = "REM"

    def detect_sleep_stage(self):
        """
        Use Yasa and the SVM model to classify sleep stage over a rolling time window.
        """
        if self.board.get_board_data_count() > 8999:
            eeg_data = self.board.get_board_data()  # Get the full board data
            self.process_eeg_data(eeg_data)

            # Yasa model processing (EOG-based REM detection)
            yasa_data_eog_left = eeg_data[self.eog_channel_left]
            yasa_data_eog_right = eeg_data[self.eog_channel_right]
            yasa_eog_comb = np.vstack([yasa_data_eog_left, yasa_data_eog_right])

            raw = RawArray(yasa_eog_comb, create_info(ch_names=["EEG", "EOG"], sfreq=self.sampling_rate, ch_types=["eeg", "eog"]))
            yasa_stages = yasa.SleepStaging(raw, eeg_name='EEG', eog_name='EOG').predict()
            self.sleep_stage = yasa_stages[-1]  # Get the most recent stage

            # Update REM count and list
            if self.sleep_stage == "REM":
                self.REM_cnt += 1
            if len(self.sleep_stage_list) >= TIME_WINDOW:
                self.sleep_stage_list.pop(0)
            self.sleep_stage_list.append(self.sleep_stage)

    def calculate_rem_period(self):
        """
        Determine if the current period falls within REM based on windowed REM calculation.
        """
        if self.REM_cnt >= TIME_WINDOW * ACCEPTED_REM_PERCENTAGE:
            return "REM_PERIOD"
        else:
            return "Not_REM_PERIOD"

    def update(self):
        """
        Main loop for updating and processing signals.
        """
        while True:
            left_eog, right_eog = self.read_eog_signal()

            if left_eog is not None and right_eog is not None:
                self.detect_eye_direction(left_eog, right_eog)  # Detect eye direction
                self.detect_sleep_stage()  # Process and detect sleep stage

                # Calculate REM Period
                rem_period = self.calculate_rem_period()

                # Print the current state with time, sleep stage, and eye movement direction
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{current_time} | Sleep Stage: {self.sleep_stage} | Eye Movement: {self.eye_direction} | REM Period: {rem_period}")

            time.sleep(0.5)  # Adjust delay for processing speed

# Flask API for interacting with the EOG detector
@app.route('/update_rem', methods=['POST'])
def update_rem():
    global rem_state
    rem_state = request.json
    return jsonify({"message": "REM state updated"}), 200

@app.route('/get_rem', methods=['GET'])
def get_rem():
    return jsonify(rem_state), 200

def main():
    eog_detector = EOGDetector()

    # Start the Flask API in a separate thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False))
    flask_thread.start()

    # Start the EOG signal processing loop
    eog_thread = Thread(target=lambda: eog_detector.update())
    eog_thread.start()

if __name__ == "__main__":
    main()
