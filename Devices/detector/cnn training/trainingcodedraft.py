# Import necessary packages
import os
import json
import numpy as np
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, LSTM, Conv1D, MaxPooling1D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

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
print(data[0])
# Encode labels
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)

label_counts = Counter(labels)
for label, count in label_counts.items():
    print(f'There are {count} data packets with the label "{label_encoder.inverse_transform([label])[0]}"')

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

# Tokenize and pad sequences
X_train = np.expand_dims(X_train, axis=-1)
X_test = np.expand_dims(X_test, axis=-1)
y_train = to_categorical(y_train, num_classes=3)
y_test = to_categorical(y_test, num_classes=3)

print('x train shape:', X_train.shape)
print('x test shape:', X_test.shape)
print('y train shape:', y_train.shape)
print('y test shape:', y_test.shape)


# Build the model
model = Sequential()
model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(max_length, 1)))
model.add(MaxPooling1D(pool_size=2))
model.add(Conv1D(filters=64, kernel_size=3, activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(Flatten())
model.add(Dense(100, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(3, activation='softmax'))  # Assuming 3 classes


model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
history = model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test), batch_size=64)

# Print shapes of the datasets
print(f"X_train shape: {X_train.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"y_test shape: {y_test.shape}")