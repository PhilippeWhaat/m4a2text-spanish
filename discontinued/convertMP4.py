import os
from moviepy.editor import *

def video_to_audio(input_path):
    # Charger le fichier vidéo
    video = VideoFileClip(input_path)
    
    # Extraire l'audio
    audio = video.audio

    # Définir le chemin de sortie
    current_directory = os.getcwd()
    output_path = os.path.join(current_directory, "input.m4a")

    # Sauvegarder l'audio dans le format souhaité
    audio.write_audiofile(output_path, codec='aac')
    
    print(f"Fichier audio sauvegardé sous: {output_path}")
    
    # Libérer les ressources
    video.close()
    audio.close()

if __name__ == '__main__':
    path = input("Entrez le chemin complet du fichier vidéo: ")
    video_to_audio(path)
