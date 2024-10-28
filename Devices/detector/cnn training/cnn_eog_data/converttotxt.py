import os
import json

# Define the file path
current_dir = os.path.dirname(__file__)
json_file_path = os.path.join(current_dir, 'old versions', 'Linjia', 'Linjia_eog_raw_slow_data.json')

# Initialize lists to store the extracted data
labels = []
eog_left_data = []
eog_right_data = []

# Open the JSON file and read the entire content
with open(json_file_path, 'r') as f:
    content = f.read()

# Split the content into individual JSON objects
json_objects = content.split('][')
json_objects[0] += ']'
json_objects[-1] = '[' + json_objects[-1]
for i in range(1, len(json_objects) - 1):
    json_objects[i] = '[' + json_objects[i] + ']'

# Parse each JSON object
for json_str in json_objects:
    try:
        obj = json.loads(json_str)
        for item in obj:
            labels.append(item['label'])
            eog_left_data.append(item['eog_left'])
            eog_right_data.append(item['eog_right'])
    except json.JSONDecodeError:
        # Handle the error or skip the object
        continue

# Now labels, eog_left_data, and eog_right_data contain the extracted data
print(f"Extracted {len(labels)} labels")
print(f"Extracted {len(eog_left_data)} eog_left data entries")
print(f"Extracted {len(eog_right_data)} eog_right data entries")
print(f"First label: {labels[101]}")
print(f"First eog_left data: {eog_left_data[101]}")
