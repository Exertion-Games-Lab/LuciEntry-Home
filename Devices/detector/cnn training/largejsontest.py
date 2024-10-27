import json

def process_chunk(chunk):
    for item in chunk:
        print(item['label'])  # Example processing

def read_large_json(file_path, chunk_size=1024):
    with open(file_path, 'r') as file:
        buffer = ''
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            buffer += chunk
            while True:
                try:
                    data, index = json.JSONDecoder().raw_decode(buffer)
                    process_chunk([data])
                    buffer = buffer[index:].lstrip()
                except json.JSONDecodeError:
                    break

if __name__ == "__main__":
    file_path = "/Users/gabriel/Documents/GitHub/LuciEntry-Home/Devices/detector/cnn training/cnn_eog_data/Gabriel/Gabriel_eog_raw_slow_data.json"
    read_large_json(file_path)