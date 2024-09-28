import os
from google.cloud import storage, speech_v1p1beta1 as speech
from pydub import AudioSegment
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Masquer la fenêtre Tkinter
Tk().withdraw()

# Demander à l'utilisateur de choisir un fichier audio
audio_file_path = askopenfilename(title="Sélectionnez un fichier audio", filetypes=[("Audio Files", "*.wav *.m4a *.mp3 *.ogg")])

# Vérifier si l'utilisateur a sélectionné un fichier
if not audio_file_path:
    print("Aucun fichier sélectionné. Fin du programme.")
    exit()

# Obtenir l'extension du fichier d'entrée
file_extension = os.path.splitext(audio_file_path)[1].lower()

# Si le fichier n'est pas en .wav, le convertir
if file_extension != ".wav":
    audio = AudioSegment.from_file(audio_file_path, format=file_extension[1:])
    audio = audio.set_channels(1)  # S'assurer qu'il est mono
    audio = audio.set_frame_rate(16000)  # S'assurer qu'il est à 16kHz
    output_file_path = "audio_temp.wav"
    audio.export(output_file_path, format="wav")
else:
    output_file_path = audio_file_path  # Pas de conversion nécessaire

# Demander le nombre de locuteurs
num_speakers = input("Entrez le nombre de locuteurs (ex. 2): ")

# Demander la langue pour la transcription
language_code = input("Entrez le code langue (ex. fr-FR, en-US, es-MX): ")

# Demander le type d'audio (video, phone_call, autre)
audio_type = input("Sélectionnez le type d'audio ('video', 'phone_call', 'autre'): ").strip().lower()

# Demander le nom du fichier de transcription
transcription_file_name = input("Entrez le nom à donner au fichier de transcription (sans l'extension) : ").strip()
transcription_file_name = transcription_file_name + ".txt"

# Définir le modèle en fonction de la sélection de l'utilisateur
if audio_type == "video":
    model_type = "video"
elif audio_type == "phone_call":
    model_type = "phone_call"
else:
    model_type = "default"  # Utiliser le modèle par défaut pour d'autres types d'audio

# Configurer Google Cloud Storage
storage_client = storage.Client()
bucket_name = "transpeach"
bucket = storage_client.bucket(bucket_name)

# Télécharger le fichier audio sur GCS
blob = bucket.blob("audio_temp.wav")
blob.upload_from_filename(output_file_path)

gcs_uri = f"gs://{bucket_name}/audio_temp.wav"

# Configurer le client Google Cloud Speech
client = speech.SpeechClient()

# Configurer les options de transcription avec diarisation
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code=language_code,
    enable_speaker_diarization=True,
    diarization_speaker_count=int(num_speakers),
    use_enhanced=False,  # Utiliser ou non le modèle amélioré
    model=model_type  # Utiliser le modèle spécifié par l'utilisateur
)

audio = speech.RecognitionAudio(uri=gcs_uri)

# Utiliser long_running_recognize pour les fichiers longs
operation = client.long_running_recognize(config=config, audio=audio)

print("Traitement en cours, cela peut prendre un certain temps...")

# Attendre la fin du traitement
response = operation.result(timeout=3600)

# Initialiser les variables pour le formatage
current_speaker = None
current_text = []

# Déterminer le chemin complet pour enregistrer le fichier de transcription
script_dir = os.path.dirname(os.path.realpath(__file__))
transcription_file_path = os.path.join(script_dir, transcription_file_name)

# Ouvrir le fichier de sortie pour la transcription formatée
with open(transcription_file_path, "w") as outfile:
    for result in response.results:
        alternative = result.alternatives[0]
        for word_info in alternative.words:
            word = word_info.word
            speaker = word_info.speaker_tag

            if current_speaker is None or speaker != current_speaker:
                if current_text:
                    outfile.write(f"Speaker {current_speaker}: {' '.join(current_text)}\n")
                current_speaker = speaker
                current_text = [word]
            else:
                current_text.append(word)

    # Écrire le dernier texte accumulé
    if current_text:
        outfile.write(f"Speaker {current_speaker}: {' '.join(current_text)}\n")

print(f"Transcription terminée et formatée. Résultats enregistrés dans '{transcription_file_path}'.")

# Nettoyage (optionnel) : supprimer le fichier de GCS après transcription
blob.delete()

# Supprimer le fichier temporaire si la conversion a eu lieu
if file_extension != ".wav":
    os.remove(output_file_path)
