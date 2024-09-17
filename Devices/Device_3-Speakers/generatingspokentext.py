import pyttsx3
from pydub import AudioSegment
from pydub.playback import play

def generate_sound_clip(prompt):
    engine = pyttsx3.init(driverName='nsss')
    
    # Set the speech rate (default is usually around 200 words per minute)
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 50)  # Decrease the rate by 50 (adjust as needed)
    
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
            # Export the sound clip as an mp3 file
            clip_filename = "sound_clip.mp3"
            engine.save_to_file(prompt, clip_filename)
            engine.runAndWait()

            print(f"Sound clip exported as {clip_filename}")
            break
        elif approval.lower() == 'n':
            # Try generating or finding a new sound clip
            engine.say("Generating new sound clip...")
            engine.runAndWait()
            # Generate a new sound clip
            new_prompt = input("Enter a new text prompt: ")
            engine.say(new_prompt)
            engine.runAndWait()
        elif approval.lower() == 'q':
            break
        else:
            print("Invalid input. Please enter 'y', 'n', or 'q'.")

    engine.stop()

# Example usage
prompt = input("Enter a text prompt: ")
generate_sound_clip(prompt)