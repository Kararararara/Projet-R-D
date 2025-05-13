import cv2
from picamera2 import Picamera2
import time
import sys

# Vérifier les arguments de la ligne de commande
if len(sys.argv) != 2:
    print("Usage: python3 contours.py <shape>")
    sys.exit(1)

target_shape = sys.argv[1]  # Forme cible à détecter
target_shape_count = 0  # Compteur pour la forme cible
target_shape_threshold = 100  # Nombre de détections consécutives nécessaires pour terminer

# Charger les images des modèles
shapes = {
    "Etoile": cv2.imread('/home/pi/Documents/opencv/star.bmp', cv2.IMREAD_GRAYSCALE),
    "Cercle": cv2.imread('/home/pi/Documents/opencv/circle.bmp', cv2.IMREAD_GRAYSCALE),
    "Triangle": cv2.imread('/home/pi/Documents/opencv/triangle.bmp', cv2.IMREAD_GRAYSCALE),
    "Losange": cv2.imread('/home/pi/Documents/opencv/diamond.bmp', cv2.IMREAD_GRAYSCALE),
    "Pentagone": cv2.imread('/home/pi/Documents/opencv/pentagon.bmp', cv2.IMREAD_GRAYSCALE),
    "Hexagone": cv2.imread('/home/pi/Documents/opencv/hexagon.bmp', cv2.IMREAD_GRAYSCALE),
    "Octogone": cv2.imread('/home/pi/Documents/opencv/cross.bmp', cv2.IMREAD_GRAYSCALE)
}

# Vérifier que les fichiers des modèles existent
for shape, image in shapes.items():
    if image is None:
        raise FileNotFoundError(f"L'image de modèle {shape} est introuvable.")

# Préparer les contours des modèles
shape_contours = {}
for shape, image in shapes.items():
    _, thresh = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        shape_contours[shape] = cv2.approxPolyDP(contours[0], 0.02 * cv2.arcLength(contours[0], True), True)
    else:
        raise ValueError(f"Impossible de trouver un contour pour le modèle {shape}.")

# Initialiser la caméra
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

detected_shapes = []  # Liste des formes détectées avec leur timestamp
detection_duration = 3  # Durée minimale de détection avant affichage (en secondes)

def filter_contours(contour, min_area=2000, max_area=100000, max_aspect_ratio=2):
    """Filtrer les contours selon leur taille et leur forme."""
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = max(w / h, h / w)
    area = cv2.contourArea(contour)
    return min_area < area < max_area and aspect_ratio < max_aspect_ratio

def match_shape(contour, model_contour):
    """Comparer un contour donné avec un contour modèle."""
    return cv2.matchShapes(contour, model_contour, cv2.CONTOURS_MATCH_I1, 0.0)

def is_circle(approx_contour):
    """Vérifier si un contour est un cercle en fonction du rapport entre son rayon et son périmètre."""
    (x, y), radius = cv2.minEnclosingCircle(approx_contour)
    area = cv2.contourArea(approx_contour)
    perimeter = cv2.arcLength(approx_contour, True)
    circularity = (4 * 3.1416 * area) / (perimeter ** 2)
    return circularity > 0.9  # Un cercle parfait aura une circularité proche de 1

def is_cross(approx_contour):
    """Vérifier si un contour est une croix (X)."""
    if len(approx_contour) != 12:
        return False
    # Vérifier les angles entre les segments pour détecter une croix
    angles = []
    for i in range(len(approx_contour)):
        p1 = approx_contour[i][0]
        p2 = approx_contour[(i + 1) % len(approx_contour)][0]
        p3 = approx_contour[(i + 2) % len(approx_contour)][0]

        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        magnitude_v1 = (v1[0]**2 + v1[1]**2)**0.5
        magnitude_v2 = (v2[0]**2 + v2[1]**2)**0.5

        if magnitude_v1 * magnitude_v2 == 0:
            return False

        angle = dot_product / (magnitude_v1 * magnitude_v2)
        angles.append(angle)

        # Une croix aura des angles spécifiques proches de 90° ou 270°
    right_angles = sum(1 for angle in angles if -0.1 < angle < 0.1)
    return right_angles >= 4

try:
    while True:
        # Capturer une image de la caméra
        frame = picam2.capture_array()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Appliquer un seuillage pour détecter les contours
        _, thresh = cv2.threshold(gray_frame, 100, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Filtrer les contours pour ignorer les bruits ou objets non pertinents
            if not filter_contours(contour):
                continue

            # Approximation pour lisser les contours
            approx_contour = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)

            # Comparer aux modèles
            best_match = None
            best_score = float('inf')

            for shape, model_contour in shape_contours.items():
                match_score = match_shape(approx_contour, model_contour)

                if match_score < best_score:
                    best_score = match_score
                    best_match = shape


            if best_match == "Etoile" and len(approx_contour) == 3:
                best_match = "Triangle"
            elif best_match == "Etoile" and len(approx_contour) == 4:
                best_match = "Losange"
            elif best_match == "Etoile" and len(approx_contour) == 5:
                best_match = "Pentagone"
            elif best_match == "Etoile" and len(approx_contour) == 6:
                best_match = "Hexagone"
            elif best_match == "Etoile" and is_cross(approx_contour) and not is_circle(approx_contour):
                best_match = "Croix"
            elif best_match == "Etoile" and 10 <= len(approx_contour) < 15:
                best_match = "Etoile"
            elif best_match == "Etoile" and (is_circle(approx_contour) or len(approx_contour) > 20) and not is_cross(approx_contour):
                best_match = "Cercle"
            else:
                best_match = None

            # Seuil pour s'assurer que le meilleur match est valide
            if best_match and best_score < 0.21:  # Ajuster le seuil
                # Dessiner un rectangle autour de la forme détectée
                x, y, w, h = cv2.boundingRect(contour)
                color = {
                    "Etoile": (0, 255, 0),
                    "Cercle": (255, 0, 0),
                    "Triangle": (0, 0, 255),
                    "Losange": (255, 255, 0),
                    "Pentagone": (0, 255, 255),
                    "Hexagone": (255, 0, 255),
                    "Croix": (128, 128, 128)
                }.get(best_match, (255, 255, 255))  # Blanc par défaut si non défini
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, best_match, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Ajouter la forme et le temps de détection si non déjà enregistrée
                if not any(shape[0] == best_match for shape in detected_shapes):
                    detected_shapes.append((best_match, time.time()))

                # Vérifier si la forme cible est détectée
                if best_match == target_shape:
                    target_shape_count += 1
                    if target_shape_count >= target_shape_threshold:
                        print(f"{target_shape} détecté - fin du programme")
                        print(best_match)  # pour que airport.py puisse le lire
                        sys.exit(0)
                else:
                    target_shape_count += 1
                    if target_shape_count >= target_shape_threshold:
                        print(best_match)
                        target_shape_count = 0  # Réinitialiser le compteur si une autre forme est détectée

        # Vérifier la durée de détection pour afficher les messages
        for shape in detected_shapes[:]:
            # Si la forme a été détectée pendant plus de 2 secondes, afficher le message
            if time.time() - shape[1] > detection_duration:
                #print(f"{shape[0]} détecté")
                detected_shapes.remove(shape)  # Enlever la forme après l'affichage

        # Afficher la vidéo avec les annotations
        cv2.imshow("Camera (Contours)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Nettoyer
    cv2.destroyAllWindows()
    picam2.stop()
