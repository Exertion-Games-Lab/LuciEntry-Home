import os
import pyttsx3
from pydub import AudioSegment
from pydub.playback import play

def generate_sound_description(prompt):
    try:
        # Initialize the TTS engine
        engine = pyttsx3.init()
        
        # Generate the sound description
        description = f"The sound of {prompt}"
        
        # Save the TTS output to a file
        tts_output_path = "tts_output.mp3"
        engine.save_to_file(description, tts_output_path)
        engine.runAndWait()
        
        # Check if the file was created
        if os.path.exists(tts_output_path):
            print(f"TTS output file created at: {tts_output_path}")
        else:
            print("Failed to create TTS output file.")
        
        return tts_output_path
    except Exception as e:
        print(f"Error generating sound description: {e}")
        return None

def play_sound_clip(prompt):
    try:
        # Generate the sound description
        tts_output_path = generate_sound_description(prompt)
        
        if tts_output_path and os.path.exists(tts_output_path):
            # Load the TTS output
            sound_clip = AudioSegment.from_mp3(tts_output_path)
            
            # Play the sound clip
            play(sound_clip)
            
            print(f"Playing generated sound for: {prompt}")
        else:
            print("No valid TTS output file to play.")
    except Exception as e:
        print(f"Error playing sound clip: {e}")

def main():
    # Get user input for the prompt
    user_prompt = input("Enter the sound you want to hear (e.g., 'whale sounds', 'forest sounds'): ")
    play_sound_clip(user_prompt)

if __name__ == "__main__":
    main()