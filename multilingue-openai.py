import os
from openai import OpenAI
from pydub import AudioSegment
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Set the API key from an environment variable
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

def process_audio_file(audio_file_path):
    # Generate the name for the transcription file based on the audio file's name
    transcription_file_name = os.path.splitext(audio_file_path)[0] + ".txt"

    # Get the file extension of the input file
    file_extension = os.path.splitext(audio_file_path)[1].lower()

    # If the file is not in .wav format, convert it
    if file_extension != ".wav":
        audio = AudioSegment.from_file(audio_file_path, format=file_extension[1:])
        audio = audio.set_channels(1)  # Ensure it is mono
        audio = audio.set_frame_rate(16000)  # Ensure it is 16kHz
        output_file_path = "audio_temp.wav"
        audio.export(output_file_path, format="wav")
    else:
        output_file_path = audio_file_path  # No conversion needed

    # Split the audio into chunks under 25 MB (~10 minutes of audio)
    chunk_size_ms = 10 * 60 * 1000  # 10 minutes in milliseconds
    audio = AudioSegment.from_wav(output_file_path)
    chunks = [audio[i:i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)]

    # Initialize the OpenAI client
    client = OpenAI()

    transcription_text = ""

    # Process each chunk
    for i, chunk in enumerate(chunks):
        chunk_path = f"chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")

        with open(chunk_path, "rb") as audio_file:
            # Perform the transcription using Whisper model
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            transcription_text += transcription + "\n"  # Directly append the response string

        os.remove(chunk_path)  # Clean up the chunk file

    # Define the post-processing function
    def generate_corrected_transcript(transcription_text_chunk, temperature=0.0):
        system_prompt = (
            "You are a helpful assistant tasked with correcting any spelling discrepancies "
            "in the transcribed text. In the same language as the text, ensure that the names of any entities, products, or "
            "technical terms are spelled correctly and apply appropriate punctuation and capitalization."
            "You don't repeat the original text or say what you are going to do, "
            "you only give the new text with the correct spelling and nothing else."
            "You give the correct text between 3 backticks, for instance: "
            "```"
            "Text in the same language with correct names of any entities, products or technical terms and appropriate punctuation and capitalization."
            "```"
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": transcription_text_chunk
                }
            ]
        )
        return response.choices[0].message.content

    # Process the transcription text in chunks if it's too long
    max_tokens_per_chunk = 2048  # Adjust this depending on the model's context window
    corrected_text = ""

    for i in range(0, len(transcription_text), max_tokens_per_chunk):
        chunk = transcription_text[i:i + max_tokens_per_chunk]
        corrected_chunk = generate_corrected_transcript(chunk)
        corrected_text += corrected_chunk + "\n"

    # Post-processing to remove unwanted text and spaces
    corrected_text = corrected_text.replace("```\n", " ").replace("```", " ").replace("\n", " ")
    while "  " in corrected_text:
        corrected_text = corrected_text.replace("  ", " ")

    # Save the corrected transcription to a file
    with open(transcription_file_name, "w") as outfile:
        outfile.write(corrected_text)

    print(f"Transcription completed and corrected. Results saved to '{transcription_file_name}'.")

    # Clean up the temporary audio file if conversion was performed
    if file_extension != ".wav":
        os.remove(output_file_path)

if __name__ == "__main__":
    # Hide the Tkinter window
    Tk().withdraw()

    # Ask the user to select an audio file
    audio_file_path = askopenfilename(title="Select an audio file", filetypes=[("Audio Files", "*.wav *.m4a *.mp3 *.ogg")])

    # Verify if the user selected a file
    if not audio_file_path:
        print("No file selected. Exiting the program.")
    else:
        process_audio_file(audio_file_path)