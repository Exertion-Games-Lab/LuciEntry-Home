import requests

def main():
    IP_ADDRESS = "192.168.1.26"
    base_url = f"http://{IP_ADDRESS}:8080"
    requests.post(f"{base_url}/command/2/VisualStimulus", {})
    requests.post(f"{base_url}/command/3/AlphaAudioStimulus", {})
    # TODO: whatever other commands you want to send

if __name__ == "__main__":
    main()
