import os
import json
import numpy as np
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, LSTM
from keras.regularizers import l2
from keras.callbacks import EarlyStopping

def load_data(data_dir):
    data = []
    labels = []
    max_length = 0
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
            combined_string = ' '.join(map(str, combined_list))
            
            data.append(combined_string)
            labels.append(entry['label'])
            
            if len(combined_list) > max_length:
                max_length = len(combined_list)
    
    return np.array(data), np.array(labels), max_length

# Load data
current_working_directory = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_working_directory, "cnn_eog_data", "data")
data, labels, max_length = load_data(data_dir)
# Preprocess data
data = [list(map(float, d.split())) for d in data]
data = np.array([np.pad(d, (0, max_length - len(d)), 'constant') for d in data])
data = data.reshape((data.shape[0], data.shape[1], 1))
# Encode labels
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)
labels = to_categorical(labels)
print(labels)
# Split data
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)
print(y_train.shape)

# Build model
model = Sequential()
model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(MaxPooling1D(pool_size=2))
model.add(Conv1D(filters=64, kernel_size=3, activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(LSTM(100))
model.add(Dropout(0.5))
model.add(Dense(100, activation='relu', kernel_regularizer=l2(0.001)))
model.add(Dropout(0.5))
model.add(Dense(3, activation='softmax', kernel_regularizer=l2(0.001)))  # Assuming 3 classes

# Compile model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Early stopping
early_stopping = EarlyStopping(monitor='val_loss', patience=50, restore_best_weights=True)

# Train model
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test), callbacks=[early_stopping])

# Evaluate model
loss, accuracy = model.evaluate(X_test, y_test)
print(f"Test Accuracy: {accuracy * 100:.2f}%")