import pyttsx3
from pydub import AudioSegment
from pydub.playback import play

def generate_sound_clip(prompt):
    engine = pyttsx3.init()
    
    # Set the speech rate (default is usually around 200 words per minute)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 100)  # Decrease the rate by 100 (adjust as needed)
    
    # List available voices
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'scottish' in voice.name.lower() and 'female' in voice.gender.lower():
            engine.setProperty('voice', voice.id)
            break
    
    engine.say(prompt)
    engine.runAndWait()

    while True:
        # Ask for approval
        approval = input("Do you approve the sound clip? (y/n/q): ")
    
        if approval.lower() == 'y':
            try:
                # Export the sound clip as an mp3 file
                clip_filename = "sound_clip.mp3"
                engine.save_to_file(prompt, clip_filename)
                engine.runAndWait()  # Process the save command
    
                print(f"Sound clip exported as {clip_filename}")
            except Exception as e:
                print(f"An error occurred: {e}")
            break
        elif approval.lower() == 'n':
            # Try generating or finding a new sound clip
            print("Generating a new sound clip...")
            # Add logic to generate a new sound clip
        elif approval.lower() == 'q':
            print("Exiting...")
            break
        else:
            print("Invalid input. Please enter 'y', 'n', or 'q'.")

    engine.stop()

# Example usage
prompt = input("Enter a text prompt: ")
generate_sound_clip(prompt)