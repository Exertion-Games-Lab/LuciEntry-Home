# Import necessary packages
import os
import json
import numpy as np
import time
from collections import Counter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, LSTM
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

def load_data(data_dir):
    data = []
    labels = []
    max_length = 0

    # First pass to determine the maximum length
    for file_name in os.listdir(data_dir):
        if file_name.endswith('.json'):
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
                    
                    # Combine both lists into one list
                    combined_list = eog_left + eog_right
                    
                    # Convert the combined list into a single string
                    combined_string = ' '.join(map(str, combined_list))
                    
                    data.append(combined_string)
                    labels.append(entry['label'])
    
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
print(labels)
# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

# Tokenize and pad sequences
tokenizer = tf.keras.preprocessing.text.Tokenizer()
tokenizer.fit_on_texts(X_train)
vocab_size = len(tokenizer.word_index) + 1
X_train = tokenizer.texts_to_sequences(X_train)
X_test = tokenizer.texts_to_sequences(X_test)
X_train = pad_sequences(X_train, maxlen=max_length*2)
X_test = pad_sequences(X_test, maxlen=max_length*2)

y_train = to_categorical(y_train, num_classes=3)
y_test = to_categorical(y_test, num_classes=3)

# Check the shape and content of the data
print(f'X_train shape: {X_train.shape}')
print(f'X_test shape: {X_test.shape}')
print(f'y_train shape: {y_train.shape}')
print(f'y_test shape: {y_test.shape}')

# Ensure labels are correctly encoded
# print(f'Unique labels in y_train: {set(y_train)}')
# print(f'Unique labels in y_test: {set(y_test)}')


# Define the model
model = tf.keras.models.Sequential([
    tf.keras.layers.Embedding(input_dim=vocab_size, output_dim=128, input_length=max_length*2),
    tf.keras.layers.Conv1D(filters=64, kernel_size=5, activation='relu'),
    tf.keras.layers.MaxPooling1D(pool_size=2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(3, activation='softmax')  # 3 units for 3 classes
])

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Train the model
model.fit(X_train, y_train, epochs=10, batch_size=32, validation_split=0.2)

# Evaluate the model
loss, accuracy = model.evaluate(X_test, y_test)
print(f'Test Accuracy: {accuracy:.2f}')

# Save the model using the SavedModel format
model.save('saved_model')

# Print the number of data packets for each label
label_counts = Counter(labels)
for label, count in label_counts.items():
    print(f'There are {count} data packets with the label "{label_encoder.inverse_transform([label])[0]}"')


