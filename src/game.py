import sys
import pygame

from player import Player
from utils import load_save, write_save
from enigma import Enigma


class Game:
    WIDTH = 900
    HEIGHT = 500
    FPS = 60

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Ruines Mythologiques - Projet B2")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        self.running = True

        # Chargement de la sauvegarde
        self.save_data = load_save()
        self.player = Player.from_dict(self.save_data.get("player", {}))

        # UI
        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

        # --- Enigme ---
        self.enigma = Enigma.sample()
        # Empêche de refaire l'énigme si déjà validée (persistant)
        self.enigma_done = bool(self.save_data.get("enigma_done", False))

        # Saisie utilisateur (mode C : texte)
        self.input_text = ""
        self.max_len = 40
        self.feedback = ""  # message de retour (correct/incorrect/indice)

    def save(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        self.save_data["enigma_done"] = self.enigma_done
        write_save(self.save_data)

    def save_and_quit(self) -> None:
        self.save()
        self.running = False

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_and_quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_and_quit()

                # Petits tests (tu peux garder)
                if event.key == pygame.K_a:
                    self.player.artifacts += 1
                    self.feedback = "Artefact +1 (test)."
                if event.key == pygame.K_l:
                    self.player.level += 1
                    self.feedback = "Niveau +1 (test)."

                # --- Saisie texte uniquement si l'énigme n'est pas déjà résolue ---
                if not self.enigma_done:
                    if event.key == pygame.K_RETURN:
                        self.validate_answer()
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_TAB:
                        # TAB = indice
                        self.feedback = f"Indice : {self.enigma.hint}" if self.enigma.hint else "Pas d'indice."
                    else:
                        # Ajouter caractère (si c'est un caractère imprimable)
                        if event.unicode and event.unicode.isprintable():
                            if len(self.input_text) < self.max_len:
                                self.input_text += event.unicode

    def validate_answer(self) -> None:
        user = self.input_text.strip()
        if not user:
            self.feedback = "Tape une réponse puis appuie sur Entrée."
            return

        if self.enigma.is_correct(user):
            self.enigma_done = True
            self.player.artifacts += 1
            self.player.rooms_unlocked = max(self.player.rooms_unlocked, 2)
            self.feedback = "✅ Correct ! Artefact obtenu et Salle II débloquée."
            self.input_text = ""
            self.save()
        else:
            self.feedback = "❌ Incorrect. Réessaie (TAB = indice)."
            self.input_text = ""

    def update(self) -> None:
        pass

    def draw_box(self, x: int, y: int, w: int, h: int) -> None:
        # Boîte de saisie simple
        pygame.draw.rect(self.screen, (40, 40, 60), (x, y, w, h), border_radius=8)
        pygame.draw.rect(self.screen, (120, 120, 160), (x, y, w, h), width=2, border_radius=8)

    def draw(self) -> None:
        self.screen.fill((15, 15, 25))

        # Titre + infos joueur
        title = self.font.render("Ruines Mythologiques - Prototype", True, (240, 240, 240))
        info1 = self.small.render("ECHAP : quitter | TAB : indice | Entrée : valider", True, (170, 170, 170))
        info2 = self.font.render(f"Joueur : {self.player.name}", True, (210, 210, 210))
        info3 = self.font.render(
            f"Niveau : {self.player.level} | Artefacts : {self.player.artifacts} | Salles : {self.player.rooms_unlocked}",
            True,
            (210, 210, 210),
        )

        self.screen.blit(title, (25, 20))
        self.screen.blit(info1, (25, 55))
        self.screen.blit(info2, (25, 90))
        self.screen.blit(info3, (25, 120))

        # Zone énigme
        y0 = 170
        if self.enigma_done:
            done = self.font.render("✅ Salle I terminée. Tu peux poursuivre l'exploration !", True, (180, 230, 180))
            self.screen.blit(done, (25, y0))
        else:
            t = self.font.render(self.enigma.title, True, (240, 220, 160))
            q = self.small.render(self.enigma.question, True, (230, 230, 230))
            self.screen.blit(t, (25, y0))
            self.screen.blit(q, (25, y0 + 35))

            # Boîte de saisie
            box_x, box_y, box_w, box_h = 25, y0 + 80, 650, 40
            self.draw_box(box_x, box_y, box_w, box_h)

            prompt = self.small.render("Réponse :", True, (200, 200, 200))
            typed = self.font.render(self.input_text, True, (255, 255, 255))

            self.screen.blit(prompt, (box_x, box_y - 22))
            self.screen.blit(typed, (box_x + 12, box_y + 8))

        # Feedback
        if self.feedback:
            fb = self.small.render(self.feedback, True, (220, 220, 220))
            self.screen.blit(fb, (25, self.HEIGHT - 35))

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
