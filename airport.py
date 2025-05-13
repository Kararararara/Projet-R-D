import speech_recognition as sr
from gtts import gTTS
import pymysql
from pymysql.connections import Connection
import os
import time
import subprocess

recognizer = sr.Recognizer()

# Itinéraires guidés par formes (comptoirs + portes)
routes = {
    "C01": [
        {"forme": "Etoile", "instruction": "Avancez tout droit", "distance": 50},
        {"forme": "Triangle", "instruction": "Tournez à droite", "distance": 20},
        {"forme": "Losange", "instruction": "Le comptoir d'embarquement C01 en face", "distance": 10}
    ],
    "C02": [
        {"forme": "Etoile", "instruction": "Avancez tout droit", "distance": 50},
        {"forme": "Triangle", "instruction": "Tournez à gauche", "distance": 20},
        {"forme": "Cercle", "instruction": "Le comptoir d'embarquement C02 à votre droite", "distance": 3}
    ],
    "P01": [
        {"forme": "Triangle", "instruction": "Tournez à gauche", "distance": 60},
        {"forme": "Hexagone", "instruction": "Tournez à gauche", "distance": 30},
        {"forme": "Octogone", "instruction": "La porte d'embarquement P01 en face", "distance": 4}
    ],
    "P02": [
        {"forme": "Triangle", "instruction": "Tournez à droite", "distance": 60},
        {"forme": "Hexagone", "instruction": "Tournez à droite", "distance": 30},
        {"forme": "Pentagone", "instruction": "La porte d'embarquement P02 en face", "distance": 5}
    ]
}

def run_contours(target_shape):
    subprocess.run(["/usr/bin/python3", "contours.py", target_shape])

# Connexion à la base de données
def creer_connexion_bdd():
    try:
        return pymysql.connect(
            host="localhost",
            user="pi",
            password=" ",
            database="airport_db"
        )
    except pymysql.MySQLError as e:
        print("Erreur lors de la connexion à la base :", e)
        return None

# Synthèse vocale
def parler(message):
    try:
        tts = gTTS(message, lang='fr')
        tts.save("message.mp3")
        os.system("mpg321 message.mp3 -q")
        os.remove("message.mp3")
        time.sleep(1)
    except Exception as e:
        print("Erreur avec gTTS :", e)

# Requête SQL d'information sur un vol
def recuperer_informations_vol(numero_vol, connexion: Connection):
    try:
        with connexion.cursor() as curseur:
            curseur.execute(
                "SELECT destination, departure_time, checkin_counter, boarding_gate "
                "FROM flights WHERE flight_number = %s",
                (numero_vol,)
            )
            resultat = curseur.fetchone()
        if resultat:
            return {
                "destination": resultat[0],
                "heure": resultat[1],
                "comptoir": resultat[2],
                "porte": resultat[3],
            }
        else:
            return None
    except pymysql.MySQLError as e:
        print("Erreur avec la base de données :", e)
        return None

# Reconnaissance vocale
def ecouter():
    with sr.Microphone() as source:
        print("Je vous écoute...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 4000

        try:
            audio = recognizer.listen(source, timeout=15, phrase_time_limit=10)
            texte = recognizer.recognize_google(audio, language="fr-FR")
            print(f"Texte capté par le micro : {texte}")
            return texte
        except sr.WaitTimeoutError:
            print("Aucun son détecté.")
            return "timeout"
        except sr.UnknownValueError:
            print("Son incompréhensible.")
            return "incompréhension"
        except sr.RequestError:
            print("Erreur de connexion au service.")
            return "erreur_requete"

# Interaction utilisateur principale
def ecouter_et_repondre(connexion: Connection):
    erreurs = 0
    while erreurs < 3:
        parler("Quel est votre numéro de vol ?")
        numero_vol = ecouter()

        if numero_vol in ["timeout", "incompréhension", "erreur_requete"]:
            erreurs += 1
            parler("Je n'ai pas bien entendu. Veuillez répéter votre numéro de vol.")
            continue

        parler(f"Vous avez bien dit le vol {numero_vol} ? Répondez par 'oui' ou 'non'.")
        confirmation = ecouter()

        if confirmation.lower() in ["oui", "oui c'est ça"]:
            infos_vol = recuperer_informations_vol(numero_vol, connexion)
            if infos_vol:
                message = (
                    f"Votre vol à destination de {infos_vol['destination']} partira à {infos_vol['heure']}."
                    f"Vous devez vous enregistrer au comptoir {infos_vol['comptoir']} puis embarquer à la porte {infos_vol['porte']}."
                    f"Dans un premier temps nous allons vous guidez à votre comptoir d'enregistrement."
                    f"Allons y."
                )
                parler(message)

                chemin_comptoir = routes.get(infos_vol['comptoir'])
                chemin_porte = routes.get(infos_vol['porte'])

                # Enchaînement du trajet vers le comptoir
                if chemin_comptoir:
                    for etape in chemin_comptoir:
                        forme = etape['forme']
                        parler(f"{etape['instruction']}.")
                        parler(f"Avancez encore {etape['distance']} mètres.")
                        run_contours(etape['forme'])

                    # Message à la fin du parcours vers le comptoir
                    parler("Vous êtes bien arrivé.")
                    parler("Quand vous avez fini de vous enregistrer, revenez sur vos pas.")

                    # Redétection de la dernière forme pour continuer
                    derniere_forme = chemin_comptoir[-1]["forme"]
                    run_contours(derniere_forme)

                    # Transition vers la porte
                    parler(f"Nous allons maintenant vous guider vers votre porte d'embarquement {infos_vol['porte']}.")

                # Puis vers la porte
                if chemin_porte:
                    for etape in chemin_porte:
                        parler(f"{etape['instruction']}.")
                        parler(f"Avancez encore {etape['distance']} mètres.")
                        run_contours(etape['forme'])

                parler("Vous êtes bien arrivé.")
                return None
            else:
                parler("Je n'ai trouvé aucune information pour ce vol.")
        elif confirmation.lower() in ["non", "non ce n'est pas ça"]:
            parler("Veuillez répéter votre numéro de vol.")
        else:
            parler("Je n'ai pas compris.")
            erreurs += 1

    parler("Je n'ai pas pu comprendre votre demande.")
    return None

# Lancement principal
def main():
    connexion = creer_connexion_bdd()
    if not connexion:
        print("Connexion échouée à la base. Arrêt.")
        return

    try:
        parler("Bonjour, bienvenue à l'aéroport Polytech Nantes.")
        ecouter_et_repondre(connexion)
    finally:
        connexion.close()

if __name__ == "__main__":
    main()
