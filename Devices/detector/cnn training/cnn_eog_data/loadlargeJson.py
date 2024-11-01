import os
import json
import re

# Define the file path
current_dir = os.path.dirname(__file__)
json_file_path = os.path.join(current_dir, 'old versions', 'Linjia', 'Linjia_eog_raw_slow_data.json')

labels = []
eog_left_data = []
eog_right_data = []

# Read the entire file content
with open(json_file_path, 'r') as f:
    file_content = f.read()

# Use a regular expression to find all JSON objects in the file
json_objects = re.findall(r'\{.*?\}', file_content, re.DOTALL)

# Process each JSON object
for json_str in json_objects:
    try:
        item = json.loads(json_str)
        labels.append(item['label'])
        eog_left_data.append(item['eog_left'])
        eog_right_data.append(item['eog_right'])
    except json.JSONDecodeError:
        # Handle the error or skip the object
        print(f"JSONDecodeError: Skipping object: {json_str}")
        continue
    except KeyError:
        # Handle the error or skip the object
        print(f"KeyError: Skipping item: {item}")
        continue

# Debug prints to check the contents before sorting
print(f"Extracted {len(labels)} labels")
print(f"Extracted {len(eog_left_data)} eog_left data entries")
print(f"Extracted {len(eog_right_data)} eog_right data entries")

# Print a small sample of the data
if labels:
    print(f"First label: {labels[0]}")
if eog_left_data:
    first_eog_left_data = eog_left_data[0]
    if first_eog_left_data:
        first_number = first_eog_left_data[0]
        second_number = first_eog_left_data[1]
        print(f"First number of the first eog_left data: {first_number}")
        print(f"Second number of the first eog_left data: {second_number}")

        # Find packets with the same first and second numbers and their indices
        matching_indices = [index for index, packet in enumerate(eog_left_data) if packet[0] == first_number and packet[1] == second_number]
        print(f"Number of matching packets: {len(matching_indices)}")
        if matching_indices:
            # Keep the first occurrence and remove subsequent duplicates
            first_occurrence = matching_indices.pop(0)
            print(f"First occurrence of matching packet: {eog_left_data[first_occurrence]} at index {first_occurrence}")

            # Remove subsequent duplicates
            for index in sorted(matching_indices, reverse=True):
                del eog_left_data[index]
                del labels[index]
                del eog_right_data[index]

        # Remove duplicates from the entire dataset
        unique_packets = set()
        indices_to_remove = []
        for index, packet in enumerate(eog_left_data):
            packet_tuple = tuple(packet)
            if packet_tuple in unique_packets:
                indices_to_remove.append(index)
            else:
                unique_packets.add(packet_tuple)

        # Remove the duplicates
        for index in sorted(indices_to_remove, reverse=True):
            del eog_left_data[index]
            del labels[index]
            del eog_right_data[index]

# Debug prints to check the contents after removal
print(f"Remaining {len(labels)} labels")
print(f"Remaining {len(eog_left_data)} eog_left data entries")
print(f"Remaining {len(eog_right_data)} eog_right data entries")

# Print a small sample of the remaining data
if labels:
    print(f"First remaining label: {labels[0]}")
if eog_left_data:
    print(f"First remaining eog_left data: {eog_left_data[0]}")
if eog_right_data:
    print(f"First remaining eog_right data: {eog_right_data[0]}")

# Sort the data if needed (example: sorting by labels)
if labels and eog_left_data and eog_right_data:
    sorted_data = sorted(zip(labels, eog_left_data, eog_right_data), key=lambda x: x[0])

    # Unzip the sorted data
    labels, eog_left_data, eog_right_data = zip(*sorted_data)

    # Now labels, eog_left_data, and eog_right_data contain the extracted and sorted data
    print(f"Sorted {len(labels)} labels")
    print(f"Sorted {len(eog_left_data)} eog_left data entries")
    print(f"Sorted {len(eog_right_data)} eog_right data entries")
else:
    print("No valid data found.")

#here
