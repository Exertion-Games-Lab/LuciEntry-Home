# Import necessary packages
import json
import os
import numpy as np
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Dropout, Input

def load_data(data_dir):
    """
    Load and preprocess data from JSON files in the specified directory.

    Parameters:
    data_dir (str): The directory containing the JSON files.

    Returns:
    tuple: A tuple containing the data and labels as numpy arrays.
    """
    data = []
    labels = []
    max_length = 0
    json_file_count = 0  # Counter for JSON files
    
    # First pass to determine the maximum length of sequences
    for file_name in os.listdir(data_dir):
        if file_name.endswith('.json'):
            json_file_count += 1
            with open(os.path.join(data_dir, file_name), 'r') as f:
                file_data = json.load(f)
                for entry in file_data:
                    max_length = max(max_length, len(entry['eog_left']), len(entry['eog_right']))
    
    # Second pass to load data and pad sequences
    for file_name in os.listdir(data_dir):
        if file_name.endswith('.json'):
            with open(os.path.join(data_dir, file_name), 'r') as f:
                file_data = json.load(f)
                for entry in file_data:
                    # Pad sequences to the maximum length
                    eog_left = entry['eog_left'] + [0] * (max_length - len(entry['eog_left']))
                    eog_right = entry['eog_right'] + [0] * (max_length - len(entry['eog_right']))
                    data.append([eog_left, eog_right])
                    labels.append(entry['label'])
    
    print(f'Number of JSON files loaded: {json_file_count}')
    return np.array(data), np.array(labels)

# Load data
current_working_directory = os.getcwd()
data_dir = os.path.join(current_working_directory, "cnn_eog_data", "data")
data, labels = load_data(data_dir)

# Print the number of data packets for each label
label_counts = Counter(labels)
for label, count in label_counts.items():
    print(f'There are {count} data packets with the label "{label}"')

# Encode labels
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)
labels = to_categorical(labels)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

# Reshape data for CNN input
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], X_train.shape[2], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], X_test.shape[2], 1)

# Verify the shape of X_train
print(f'Shape of X_train: {X_train.shape}')

# Ensure X_train has the correct shape (num_samples, height, width, channels)
# If X_train is missing the channel dimension, add it
if len(X_train.shape) == 3:
    X_train = np.expand_dims(X_train, axis=-1)
    X_test = np.expand_dims(X_test, axis=-1)

# Verify the shape again after adding the channel dimension
print(f'Shape of X_train after adding channel dimension: {X_train.shape}')

# Reshape the data to have a suitable height and width for convolutional layers
X_train = X_train.reshape(X_train.shape[0], X_train.shape[2], X_train.shape[1] * X_train.shape[3])
X_test = X_test.reshape(X_test.shape[0], X_test.shape[2], X_test.shape[1] * X_test.shape[3])

# Verify the new shape
print(f'Shape of X_train after reshaping: {X_train.shape}')

# Define the model
model = Sequential([
    Input(shape=(X_train.shape[1], X_train.shape[2])),
    Conv1D(32, 3, activation='relu'),
    MaxPooling1D(2),
    Conv1D(64, 3, activation='relu'),
    MaxPooling1D(2),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(len(label_encoder.classes_), activation='softmax')
])

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

# Evaluate the model
loss, accuracy = model.evaluate(X_test, y_test)
print(f'Test accuracy: {accuracy}')

# Save the model
model.save('cnn_eog_model.h5')
print('Model saved as cnn_eog_model.h5')

