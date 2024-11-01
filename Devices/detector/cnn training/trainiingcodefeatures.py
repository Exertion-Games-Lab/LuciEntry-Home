import os
import json
import numpy as np
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, Input
from keras.callbacks import EarlyStopping
from collections import Counter
from scipy.stats import skew, kurtosis
from scipy.signal import welch

def extract_features(data_packet): 
    features = []
    
    # Split the data packet into left and right EOG signals
    left_eog = data_packet[:250]
    right_eog = data_packet[250:]
    
    # Statistical features
    for signal in [left_eog, right_eog]:
        signal = np.array(signal)
        features.append(np.mean(signal))
        features.append(np.std(signal))
        features.append(np.var(signal))
        features.append(skew(signal))
        features.append(kurtosis(signal))
        freqs, psd = welch(signal)
        features.append(np.sum(psd))  # Power spectral density
        features.append(freqs[np.argmax(psd)])  # Dominant frequency
        features.append(-np.sum(psd * np.log(psd)))
        features.append(np.sum(np.diff(np.sign(signal)) != 0)) 
         # Additional features
        features.append(np.median(signal))
        features.append(np.min(signal))
        features.append(np.max(signal))
        features.append(np.ptp(signal))  # Peak-to-peak range
        features.append(np.percentile(signal, 25))  # 25th percentile
        features.append(np.percentile(signal, 75))  # 75th percentile
        features.append(np.trapz(signal))  # Area under the curve
        features.append(np.mean(np.diff(signal)))  # Mean of the first difference
        features.append(np.mean(np.abs(np.diff(signal))))  # Mean absolute difference
        features.append(np.mean(np.diff(signal, n=2)))  # Mean of the second difference
        features.append(np.mean(np.abs(np.diff(signal, n=2))))  # Mean absolute second difference
        features.append(np.sum(signal ** 2))  # Energy
        features.append(np.sqrt(np.mean(signal ** 2)))  # Root mean square
        features.append(np.mean(np.abs(signal)))  # Mean absolute value
        features.append(np.mean(signal ** 3))  # Skewness (alternative)
        features.append(np.mean(signal ** 4))  # Kurtosis (alternative)
        features.append(np.sum(np.abs(np.diff(signal)) > 0.1))  # Number of large changes
        features.append(np.sum(np.abs(np.diff(signal, n=2)) > 0.1))  # Number of large second differences
        
    
    return features

def load_data(data_dir): # replace with code that loads the larger raw json files into in chunks
    data = []
    labels = []
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    print(f"Number of JSON files being processed: {len(json_files)}")
    
    for file_name in json_files:
        file_path = os.path.join(data_dir, file_name)
        with open(file_path, 'r') as f:
            file_data = json.load(f)
        
        for entry in file_data:
            eog_left = entry['eog_left']
            eog_right = entry['eog_right']
            combined_list = eog_left + eog_right
            
            features = extract_features(combined_list)
            data.append(features)
            labels.append(entry['label'])
            

    label_counts = Counter(labels)
    for label, count in label_counts.items():
        print(f"Class '{label}' has {count} data packets.")
    
    return np.array(data), np.array(labels)

# Load data
current_working_directory = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_working_directory, "cnn_eog_data", "data")
data, labels = load_data(data_dir)

print('data shape :',data.shape)
print('labels shape :',labels.shape)
print ('first data packet',data[0])
print ('first label', labels[0])


# Encode labels
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)
labels = to_categorical(labels)

# Split data
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.4, random_state=42)

# Print shapes for debugging
print('y train shape:', y_train.shape)
print('X train shape:', X_train.shape)


# Build model
model = Sequential()
model.add(Input(shape=(X_train.shape[1], 1)))
model.add(Conv1D(filters=64, kernel_size=3, activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(Conv1D(filters=64, kernel_size=3, activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(Flatten())
model.add(Dense(100, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(3, activation='softmax'))  # Assuming 3 classes


# Compile model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Early stopping
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# Train model
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), callbacks=[early_stopping])

# Evaluate model
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy * 100:.2f}%")