"""
Simulateur de Conduite - Permis B
Voiture française standard manuelle
Clavier AZERTY français

Contrôles:
- Embrayage: A, Z, E, R (progressif, maintenir les touches précédentes)
- Frein: Q, S, D, F (progressif, maintenir les touches précédentes)
- Accélérateur: W, X, C, V (progressif, maintenir les touches précédentes)
- Vitesses: 1-5 pour les vitesses, 0 pour point mort, N pour marche arrière
- Flèches gauche/droite: Direction
- Espace: Frein à main
- Entrée: Démarrer/Couper le moteur
"""

import pygame
import math
import sys

# Initialisation de Pygame
pygame.init()

# Configuration de l'écran
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulateur de Conduite - Permis B")

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
ROAD_GRAY = (70, 70, 70)
DASHBOARD_BROWN = (101, 67, 33)
PEDAL_GRAY = (50, 50, 50)

# Polices
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 32)
font_large = pygame.font.Font(None, 48)
font_title = pygame.font.Font(None, 64)

# Classe Voiture
class Voiture:
    def __init__(self):
        self.moteur_demarre = False
        self.vitesse_actuelle = 0  # km/h
        self.regime_moteur = 800  # RPM au ralenti
        self.vitesse_engagee = 0  # 0 = point mort, 1-5 = vitesses, -1 = marche arrière
        self.embrayage = 0  # 0-4 (0 = relâché, 4 = enfoncé à fond)
        self.frein = 0  # 0-4
        self.accelerateur = 0  # 0-4
        self.direction = 0  # -1 gauche, 0 centre, 1 droite
        self.frein_main = True
        self.position_route = 0  # Position sur la route (pour l'animation)
        self.position_laterale = 0  # Position latérale (-100 à 100)
        self.cale = False

        # Plages de régime pour chaque vitesse (min optimal, max optimal)
        self.plages_regime = {
            1: (1000, 2500),
            2: (1500, 3000),
            3: (2000, 3500),
            4: (2500, 4000),
            5: (3000, 4500),
        }

        # Vitesses max par rapport
        self.vitesse_max_rapport = {
            -1: 20,
            1: 30,
            2: 50,
            3: 70,
            4: 100,
            5: 130,
        }

    def update(self, dt):
        if not self.moteur_demarre:
            self.regime_moteur = 0
            return

        # Calcul du régime moteur
        if self.vitesse_engagee == 0:  # Point mort
            regime_cible = 800 + (self.accelerateur * 1500)
        else:
            # Régime basé sur la vitesse et le rapport engagé
            if self.vitesse_engagee > 0:
                rapport = self.vitesse_engagee
                vitesse_max = self.vitesse_max_rapport[rapport]
                regime_base = 800 + (self.vitesse_actuelle / vitesse_max) * 5200
            else:  # Marche arrière
                regime_base = 800 + (abs(self.vitesse_actuelle) / 20) * 3000

            # Influence de l'accélérateur
            if self.embrayage >= 3:  # Embrayage suffisamment enfoncé
                regime_cible = 800 + (self.accelerateur * 1500)
            else:
                regime_cible = regime_base + (self.accelerateur * 500)

        # Transition douce du régime
        self.regime_moteur += (regime_cible - self.regime_moteur) * dt * 3
        self.regime_moteur = max(0, min(7000, self.regime_moteur))

        # Détection du calage
        if self.vitesse_engagee != 0 and self.embrayage < 2:
            if self.regime_moteur < 500 and self.vitesse_actuelle < 5:
                self.cale = True
                self.moteur_demarre = False
                self.regime_moteur = 0

        # Calcul de la vitesse
        if self.vitesse_engagee != 0 and self.embrayage < 4:
            # Force motrice (dépend du régime et de l'embrayage)
            coeff_embrayage = 1 - (self.embrayage / 4)
            force_motrice = (self.accelerateur / 4) * coeff_embrayage

            if self.vitesse_engagee > 0:
                vitesse_cible = force_motrice * self.vitesse_max_rapport[self.vitesse_engagee]
            else:  # Marche arrière
                vitesse_cible = -force_motrice * 20

            # Accélération/décélération
            if not self.frein_main:
                acceleration = (vitesse_cible - self.vitesse_actuelle) * dt * 2
                self.vitesse_actuelle += acceleration

        # Freinage
        if self.frein > 0:
            freinage = self.frein * 30 * dt
            if self.vitesse_actuelle > 0:
                self.vitesse_actuelle = max(0, self.vitesse_actuelle - freinage)
            elif self.vitesse_actuelle < 0:
                self.vitesse_actuelle = min(0, self.vitesse_actuelle + freinage)

        # Frein à main
        if self.frein_main and abs(self.vitesse_actuelle) > 0:
            self.vitesse_actuelle *= 0.95
            if abs(self.vitesse_actuelle) < 0.5:
                self.vitesse_actuelle = 0

        # Friction naturelle
        if self.accelerateur == 0 and self.vitesse_engagee == 0:
            self.vitesse_actuelle *= 0.99

        # Mise à jour de la position
        self.position_route += self.vitesse_actuelle * dt * 10

        # Direction
        if abs(self.vitesse_actuelle) > 1:
            self.position_laterale += self.direction * abs(self.vitesse_actuelle) * dt * 0.5
            self.position_laterale = max(-100, min(100, self.position_laterale))

    def demarrer_moteur(self):
        if not self.moteur_demarre and self.embrayage >= 3:
            self.moteur_demarre = True
            self.cale = False
            self.regime_moteur = 800
            return True
        return False

    def couper_moteur(self):
        self.moteur_demarre = False
        self.regime_moteur = 0

    def changer_vitesse(self, nouvelle_vitesse):
        if self.embrayage >= 3:  # Embrayage enfoncé suffisamment
            self.vitesse_engagee = nouvelle_vitesse
            return True
        return False


# Classe Tutoriel
class Tutoriel:
    def __init__(self):
        self.etape = 0
        self.etapes = [
            {
                "titre": "Bienvenue au Simulateur de Conduite !",
                "texte": [
                    "Apprenez à conduire une voiture manuelle.",
                    "",
                    "Contrôles des pédales (progressifs) :",
                    "- Embrayage : A, Z, E, R (de léger à fond)",
                    "- Frein : Q, S, D, F",
                    "- Accélérateur : W, X, C, V",
                    "",
                    "Appuyez sur ESPACE pour continuer..."
                ],
                "condition": lambda v: True
            },
            {
                "titre": "Étape 1 : Vérifications avant démarrage",
                "texte": [
                    "Avant de démarrer :",
                    "1. Vérifiez que le frein à main est serré (case verte)",
                    "2. Vérifiez que vous êtes au point mort (N sur l'indicateur)",
                    "",
                    "Le frein à main est actuellement SERRÉ.",
                    "Appuyez sur 0 pour mettre au point mort si nécessaire.",
                    "",
                    "Appuyez sur ESPACE quand c'est fait..."
                ],
                "condition": lambda v: v.frein_main and v.vitesse_engagee == 0
            },
            {
                "titre": "Étape 2 : Démarrer le moteur",
                "texte": [
                    "Pour démarrer le moteur :",
                    "1. Enfoncez l'embrayage à fond (A+Z+E+R)",
                    "2. Appuyez sur ENTRÉE pour démarrer",
                    "",
                    "Maintenez A, puis ajoutez Z, E, et R",
                    "L'indicateur d'embrayage doit être au maximum.",
                    "",
                    "Démarrez le moteur..."
                ],
                "condition": lambda v: v.moteur_demarre
            },
            {
                "titre": "Étape 3 : Engager la première vitesse",
                "texte": [
                    "Moteur démarré ! Maintenant :",
                    "1. Gardez l'embrayage enfoncé (A+Z+E+R)",
                    "2. Appuyez sur 1 pour la première vitesse",
                    "",
                    "L'indicateur de vitesse passera de N à 1.",
                    "",
                    "Engagez la première..."
                ],
                "condition": lambda v: v.vitesse_engagee == 1
            },
            {
                "titre": "Étape 4 : Desserrer le frein à main",
                "texte": [
                    "Parfait ! Première engagée.",
                    "",
                    "Appuyez sur ESPACE pour desserrer",
                    "le frein à main.",
                    "",
                    "Gardez l'embrayage enfoncé !",
                ],
                "condition": lambda v: not v.frein_main
            },
            {
                "titre": "Étape 5 : Démarrer en douceur",
                "texte": [
                    "C'est le moment délicat !",
                    "",
                    "1. Accélérez légèrement (W)",
                    "2. Relâchez DOUCEMENT l'embrayage",
                    "   (lâchez R, puis E, puis Z...)",
                    "",
                    "Si vous calez, recommencez !",
                    "Objectif : atteindre 10 km/h"
                ],
                "condition": lambda v: v.vitesse_actuelle >= 10
            },
            {
                "titre": "Bravo ! Vous roulez !",
                "texte": [
                    "Félicitations ! Vous avez réussi à démarrer !",
                    "",
                    "Continuez à pratiquer :",
                    "- Passez la 2ème vers 20 km/h",
                    "- Utilisez les flèches pour tourner",
                    "- Freinez avec Q, S, D, F",
                    "",
                    "Bonne route !"
                ],
                "condition": lambda v: True
            }
        ]
        self.afficher = True

    def verifier_etape(self, voiture):
        if self.etape < len(self.etapes) - 1:
            if self.etapes[self.etape]["condition"](voiture):
                pass  # Condition remplie, on peut passer à la suite

    def etape_suivante(self, voiture):
        if self.etape < len(self.etapes) - 1:
            if self.etapes[self.etape]["condition"](voiture):
                self.etape += 1

    def get_etape_actuelle(self):
        return self.etapes[self.etape]


# Fonctions de dessin
def dessiner_ciel(screen, position_route):
    """Dessine le ciel avec des nuages"""
    screen.fill(SKY_BLUE, (0, 0, SCREEN_WIDTH, 300))

    # Soleil
    pygame.draw.circle(screen, YELLOW, (100, 80), 40)

    # Nuages (se déplacent avec la route)
    offset = int(position_route * 0.1) % 400
    for i in range(5):
        x = (i * 300 - offset) % 1500 - 100
        pygame.draw.ellipse(screen, WHITE, (x, 50 + (i % 3) * 30, 120, 40))
        pygame.draw.ellipse(screen, WHITE, (x + 30, 40 + (i % 3) * 30, 80, 50))
        pygame.draw.ellipse(screen, WHITE, (x + 60, 50 + (i % 3) * 30, 100, 40))


def dessiner_paysage(screen, position_route):
    """Dessine le paysage (herbe, arbres)"""
    # Herbe
    pygame.draw.rect(screen, GRASS_GREEN, (0, 250, SCREEN_WIDTH, 100))

    # Arbres (se déplacent avec la route)
    offset = int(position_route * 0.5) % 200
    for i in range(10):
        x = (i * 200 - offset) % 1600 - 100
        # Tronc
        pygame.draw.rect(screen, DASHBOARD_BROWN, (x + 15, 230, 20, 50))
        # Feuillage
        pygame.draw.polygon(screen, (0, 100, 0), [(x, 240), (x + 25, 180), (x + 50, 240)])
        pygame.draw.polygon(screen, (0, 120, 0), [(x + 5, 220), (x + 25, 160), (x + 45, 220)])


def dessiner_route(screen, position_route, position_laterale):
    """Dessine la route en perspective"""
    # Route principale
    points_route = [
        (400 + position_laterale, 350),  # Haut gauche
        (880 + position_laterale, 350),  # Haut droit
        (SCREEN_WIDTH + 200, 500),  # Bas droit
        (-200, 500),  # Bas gauche
    ]
    pygame.draw.polygon(screen, ROAD_GRAY, points_route)

    # Lignes blanches sur les côtés
    pygame.draw.line(screen, WHITE, (400 + position_laterale, 350), (-200, 500), 3)
    pygame.draw.line(screen, WHITE, (880 + position_laterale, 350), (SCREEN_WIDTH + 200, 500), 3)

    # Ligne centrale pointillée
    offset = int(position_route) % 60
    for i in range(15):
        y1 = 350 + i * 15 - offset * 0.25
        y2 = y1 + 10
        if y1 < 350:
            continue
        if y2 > 500:
            break
        # Calcul de la position X en fonction de Y (perspective)
        ratio = (y1 - 350) / 150
        x = 640 + position_laterale * (1 - ratio * 0.5)
        largeur = 3 + ratio * 5
        pygame.draw.line(screen, WHITE, (x, y1), (x, min(y2, 500)), int(largeur))


def dessiner_tableau_bord(screen, voiture):
    """Dessine le tableau de bord"""
    # Fond du tableau de bord
    pygame.draw.rect(screen, DASHBOARD_BROWN, (0, 500, SCREEN_WIDTH, 220))
    pygame.draw.rect(screen, DARK_GRAY, (0, 500, SCREEN_WIDTH, 10))

    # Compteur de vitesse (à gauche)
    centre_vitesse = (250, 600)
    pygame.draw.circle(screen, BLACK, centre_vitesse, 80)
    pygame.draw.circle(screen, WHITE, centre_vitesse, 75, 2)

    # Graduations vitesse
    for i in range(0, 140, 20):
        angle = math.radians(225 - i * 1.9)
        x1 = centre_vitesse[0] + math.cos(angle) * 65
        y1 = centre_vitesse[1] - math.sin(angle) * 65
        x2 = centre_vitesse[0] + math.cos(angle) * 55
        y2 = centre_vitesse[1] - math.sin(angle) * 55
        pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), 2)

        # Chiffres
        text = font_small.render(str(i), True, WHITE)
        tx = centre_vitesse[0] + math.cos(angle) * 45 - text.get_width() // 2
        ty = centre_vitesse[1] - math.sin(angle) * 45 - text.get_height() // 2
        screen.blit(text, (tx, ty))

    # Aiguille vitesse
    vitesse_affichee = max(0, min(130, voiture.vitesse_actuelle))
    angle_aiguille = math.radians(225 - vitesse_affichee * 1.9)
    x_aiguille = centre_vitesse[0] + math.cos(angle_aiguille) * 50
    y_aiguille = centre_vitesse[1] - math.sin(angle_aiguille) * 50
    pygame.draw.line(screen, RED, centre_vitesse, (x_aiguille, y_aiguille), 3)
    pygame.draw.circle(screen, RED, centre_vitesse, 8)

    # Texte km/h
    text_kmh = font_small.render("km/h", True, WHITE)
    screen.blit(text_kmh, (centre_vitesse[0] - text_kmh.get_width() // 2, centre_vitesse[1] + 30))

    # Compte-tours (à droite)
    centre_rpm = (500, 600)
    pygame.draw.circle(screen, BLACK, centre_rpm, 80)
    pygame.draw.circle(screen, WHITE, centre_rpm, 75, 2)

    # Zone rouge
    for i in range(60, 70):
        angle = math.radians(225 - i * 4)
        x1 = centre_rpm[0] + math.cos(angle) * 70
        y1 = centre_rpm[1] - math.sin(angle) * 70
        x2 = centre_rpm[0] + math.cos(angle) * 55
        y2 = centre_rpm[1] - math.sin(angle) * 55
        pygame.draw.line(screen, RED, (x1, y1), (x2, y2), 3)

    # Graduations RPM
    for i in range(0, 8):
        angle = math.radians(225 - i * 33.75)
        x1 = centre_rpm[0] + math.cos(angle) * 65
        y1 = centre_rpm[1] - math.sin(angle) * 65
        x2 = centre_rpm[0] + math.cos(angle) * 55
        y2 = centre_rpm[1] - math.sin(angle) * 55
        pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), 2)

        text = font_small.render(str(i), True, WHITE)
        tx = centre_rpm[0] + math.cos(angle) * 45 - text.get_width() // 2
        ty = centre_rpm[1] - math.sin(angle) * 45 - text.get_height() // 2
        screen.blit(text, (tx, ty))

    # Aiguille RPM
    rpm_affiche = max(0, min(7000, voiture.regime_moteur))
    angle_rpm = math.radians(225 - (rpm_affiche / 1000) * 33.75)
    x_rpm = centre_rpm[0] + math.cos(angle_rpm) * 50
    y_rpm = centre_rpm[1] - math.sin(angle_rpm) * 50
    pygame.draw.line(screen, RED, centre_rpm, (x_rpm, y_rpm), 3)
    pygame.draw.circle(screen, RED, centre_rpm, 8)

    # Texte x1000 RPM
    text_rpm = font_small.render("x1000 RPM", True, WHITE)
    screen.blit(text_rpm, (centre_rpm[0] - text_rpm.get_width() // 2, centre_rpm[1] + 30))

    # Indicateur de vitesse engagée
    pygame.draw.rect(screen, BLACK, (620, 550, 60, 80))
    pygame.draw.rect(screen, WHITE, (620, 550, 60, 80), 2)

    if voiture.vitesse_engagee == 0:
        vitesse_txt = "N"
    elif voiture.vitesse_engagee == -1:
        vitesse_txt = "R"
    else:
        vitesse_txt = str(voiture.vitesse_engagee)

    text_vitesse = font_title.render(vitesse_txt, True, GREEN if voiture.moteur_demarre else RED)
    screen.blit(text_vitesse, (650 - text_vitesse.get_width() // 2, 575))

    # Indicateurs
    # Frein à main
    frein_main_color = GREEN if voiture.frein_main else DARK_GRAY
    pygame.draw.rect(screen, frein_main_color, (700, 560, 40, 30))
    text_fm = font_small.render("P", True, BLACK)
    screen.blit(text_fm, (712, 565))

    # Moteur
    moteur_color = GREEN if voiture.moteur_demarre else RED
    pygame.draw.circle(screen, moteur_color, (760, 575), 15)

    # Calé
    if voiture.cale:
        text_cale = font_medium.render("CALÉ !", True, RED)
        screen.blit(text_cale, (SCREEN_WIDTH // 2 - text_cale.get_width() // 2, 520))


def dessiner_pedales(screen, voiture):
    """Dessine les pédales avec leurs niveaux"""
    # Zone des pédales
    pygame.draw.rect(screen, DARK_GRAY, (850, 520, 400, 180))

    # Embrayage (gauche)
    dessiner_pedale(screen, 900, 540, "EMBRAYAGE", voiture.embrayage, ["A", "Z", "E", "R"], BLUE)

    # Frein (centre)
    dessiner_pedale(screen, 1000, 540, "FREIN", voiture.frein, ["Q", "S", "D", "F"], RED)

    # Accélérateur (droite)
    dessiner_pedale(screen, 1100, 540, "ACCEL", voiture.accelerateur, ["W", "X", "C", "V"], GREEN)


def dessiner_pedale(screen, x, y, nom, niveau, touches, couleur):
    """Dessine une pédale individuelle"""
    # Nom de la pédale
    text_nom = font_small.render(nom, True, WHITE)
    screen.blit(text_nom, (x - text_nom.get_width() // 2, y))

    # Barre de niveau
    pygame.draw.rect(screen, DARK_GRAY, (x - 15, y + 25, 30, 100))
    pygame.draw.rect(screen, WHITE, (x - 15, y + 25, 30, 100), 1)

    # Niveau actuel
    hauteur_niveau = niveau * 25
    if hauteur_niveau > 0:
        pygame.draw.rect(screen, couleur, (x - 13, y + 123 - hauteur_niveau, 26, hauteur_niveau))

    # Touches
    for i, touche in enumerate(touches):
        ty = y + 130 + i * 18
        actif = niveau > i
        bg_color = couleur if actif else DARK_GRAY
        pygame.draw.rect(screen, bg_color, (x - 12, ty, 24, 16))
        pygame.draw.rect(screen, WHITE, (x - 12, ty, 24, 16), 1)

        text_touche = font_small.render(touche, True, WHITE if actif else GRAY)
        screen.blit(text_touche, (x - text_touche.get_width() // 2, ty + 1))


def dessiner_tutoriel(screen, tutoriel):
    """Dessine le panneau de tutoriel"""
    if not tutoriel.afficher:
        return

    etape = tutoriel.get_etape_actuelle()

    # Fond semi-transparent
    s = pygame.Surface((500, 300))
    s.set_alpha(230)
    s.fill(DARK_GRAY)
    screen.blit(s, (20, 20))

    # Bordure
    pygame.draw.rect(screen, WHITE, (20, 20, 500, 300), 2)

    # Titre
    text_titre = font_medium.render(etape["titre"], True, YELLOW)
    screen.blit(text_titre, (30, 30))

    # Texte
    y_texte = 70
    for ligne in etape["texte"]:
        text_ligne = font_small.render(ligne, True, WHITE)
        screen.blit(text_ligne, (30, y_texte))
        y_texte += 25

    # Indicateur d'étape
    text_etape = font_small.render(f"Étape {tutoriel.etape + 1}/{len(tutoriel.etapes)}", True, GRAY)
    screen.blit(text_etape, (30, 290))

    # Instruction pour masquer
    text_masquer = font_small.render("T: Masquer/Afficher tutoriel", True, GRAY)
    screen.blit(text_masquer, (350, 290))


def dessiner_aide_touches(screen):
    """Dessine l'aide des touches"""
    aide = [
        "ENTRÉE: Démarrer/Couper moteur",
        "ESPACE: Frein à main",
        "0-5: Vitesses (0=N, 1-5)",
        "N: Marche arrière",
        "←→: Direction",
        "ESC: Quitter"
    ]

    y = 340
    for ligne in aide:
        text = font_small.render(ligne, True, WHITE)
        # Fond semi-transparent
        s = pygame.Surface((text.get_width() + 10, text.get_height() + 4))
        s.set_alpha(150)
        s.fill(BLACK)
        screen.blit(s, (SCREEN_WIDTH - text.get_width() - 15, y - 2))
        screen.blit(text, (SCREEN_WIDTH - text.get_width() - 10, y))
        y += 22


def gerer_pedales(keys, voiture):
    """Gère les entrées clavier pour les pédales (système progressif)"""
    # Embrayage: A, Z, E, R
    embrayage = 0
    if keys[pygame.K_a]:
        embrayage = 1
        if keys[pygame.K_z]:
            embrayage = 2
            if keys[pygame.K_e]:
                embrayage = 3
                if keys[pygame.K_r]:
                    embrayage = 4
    voiture.embrayage = embrayage

    # Frein: Q, S, D, F
    frein = 0
    if keys[pygame.K_q]:
        frein = 1
        if keys[pygame.K_s]:
            frein = 2
            if keys[pygame.K_d]:
                frein = 3
                if keys[pygame.K_f]:
                    frein = 4
    voiture.frein = frein

    # Accélérateur: W, X, C, V
    accelerateur = 0
    if keys[pygame.K_w]:
        accelerateur = 1
        if keys[pygame.K_x]:
            accelerateur = 2
            if keys[pygame.K_c]:
                accelerateur = 3
                if keys[pygame.K_v]:
                    accelerateur = 4
    voiture.accelerateur = accelerateur

    # Direction
    voiture.direction = 0
    if keys[pygame.K_LEFT]:
        voiture.direction = -1
    elif keys[pygame.K_RIGHT]:
        voiture.direction = 1


def main():
    """Fonction principale"""
    clock = pygame.time.Clock()
    voiture = Voiture()
    tutoriel = Tutoriel()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0  # Delta time en secondes

        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                # Quitter
                if event.key == pygame.K_ESCAPE:
                    running = False

                # Démarrer/Couper le moteur
                elif event.key == pygame.K_RETURN:
                    if voiture.moteur_demarre:
                        voiture.couper_moteur()
                    else:
                        voiture.demarrer_moteur()

                # Frein à main
                elif event.key == pygame.K_SPACE:
                    if tutoriel.etape == 0 or tutoriel.etape == 1:
                        tutoriel.etape_suivante(voiture)
                    else:
                        voiture.frein_main = not voiture.frein_main

                # Vitesses
                elif event.key == pygame.K_0:
                    voiture.changer_vitesse(0)  # Point mort
                elif event.key == pygame.K_1:
                    voiture.changer_vitesse(1)
                elif event.key == pygame.K_2:
                    voiture.changer_vitesse(2)
                elif event.key == pygame.K_3:
                    voiture.changer_vitesse(3)
                elif event.key == pygame.K_4:
                    voiture.changer_vitesse(4)
                elif event.key == pygame.K_5:
                    voiture.changer_vitesse(5)
                elif event.key == pygame.K_n:
                    voiture.changer_vitesse(-1)  # Marche arrière

                # Tutoriel
                elif event.key == pygame.K_t:
                    tutoriel.afficher = not tutoriel.afficher

        # Gestion des touches maintenues (pédales)
        keys = pygame.key.get_pressed()
        gerer_pedales(keys, voiture)

        # Mise à jour de la voiture
        voiture.update(dt)

        # Vérification des étapes du tutoriel
        tutoriel.verifier_etape(voiture)
        if tutoriel.etape >= 2:  # Après les étapes initiales
            tutoriel.etape_suivante(voiture)

        # Dessin
        dessiner_ciel(screen, voiture.position_route)
        dessiner_paysage(screen, voiture.position_route)
        dessiner_route(screen, voiture.position_route, voiture.position_laterale)
        dessiner_tableau_bord(screen, voiture)
        dessiner_pedales(screen, voiture)
        dessiner_aide_touches(screen)
        dessiner_tutoriel(screen, tutoriel)

        # Rafraîchissement de l'écran
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
