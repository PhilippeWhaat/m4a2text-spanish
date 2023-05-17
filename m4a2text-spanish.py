import os
import speech_recognition as sr
from pydub import AudioSegment

PATHPY = os.path.realpath(__file__)

def convert_m4a_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file, format="m4a")
    audio.export(output_file, format="wav")

def transcribe_audio(file_path, language='es-ES', chunk_length=30000):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(file_path)

    chunks = []

    # Split the audio into chunks of chunk_length milliseconds
    for i in range(0, len(audio), chunk_length):
        chunks.append(audio[i:i + chunk_length])

    transcription = []

    for idx, chunk in enumerate(chunks):
        chunk.export("temp_chunk.wav", format="wav")

        with sr.AudioFile("temp_chunk.wav") as source:
            audio_data = recognizer.record(source)

        try:
            chunk_transcription = recognizer.recognize_google(audio_data, language=language)
            if chunk_transcription is None or chunk_transcription == '':
                print(f"Error in chunk {idx + 1}: No transcription returned")
            else:
                transcription.append(chunk_transcription)
        except sr.UnknownValueError:
            print(f"Error in chunk {idx + 1}: Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Error in chunk {idx + 1}: Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            print(f"Error in chunk {idx + 1}: {e}")

        os.remove("temp_chunk.wav")

    return " ".join(transcription)


def main():
    input_file = os.path.join(os.path.dirname(PATHPY), "input.m4a")
    output_file = os.path.join(os.path.dirname(PATHPY), "output.wav")
    transcription_file = os.path.join(os.path.dirname(PATHPY), "transcription.txt")

    # Convert M4A to WAV
    convert_m4a_to_wav(input_file, output_file)

    # Transcribe audio
    transcription = transcribe_audio(output_file)

    if transcription:
        # Save transcription to a text file
        with open(transcription_file, 'w', encoding='utf-8') as f:
            f.write(transcription)

        print(f"Transcription saved to {transcription_file}")
    else:
        print("Transcription failed.")

    # Remove temporary WAV file
    os.remove(output_file)

if __name__ == "__main__":
    main()