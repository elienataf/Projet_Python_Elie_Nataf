import sys
import pygame

from player import Player
from utils import load_save, write_save


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

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_and_quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_and_quit()

                # TESTS PERSISTANCE
                if event.key == pygame.K_a:
                    self.player.artifacts += 1

                if event.key == pygame.K_l:
                    self.player.level += 1

    def update(self) -> None:
        # Logique du jeu (plus tard : énigmes, salles, artefacts)
        pass

    def draw(self) -> None:
        self.screen.fill((15, 15, 25))

        title = self.font.render(
            "Ruines Mythologiques - Prototype", True, (240, 240, 240)
        )
        info1 = self.font.render("ECHAP : quitter", True, (200, 200, 200))
        info2 = self.font.render(f"Joueur : {self.player.name}", True, (200, 200, 200))
        info3 = self.font.render(
            f"Niveau : {self.player.level} | Artefacts : {self.player.artifacts}",
            True,
            (200, 200, 200),
        )
        info4 = self.font.render(
            "A : +1 artefact | L : +1 niveau (test sauvegarde)",
            True,
            (160, 160, 160),
        )

        self.screen.blit(title, (25, 25))
        self.screen.blit(info1, (25, 65))
        self.screen.blit(info2, (25, 95))
        self.screen.blit(info3, (25, 125))
        self.screen.blit(info4, (25, 155))

        pygame.display.flip()

    def save_and_quit(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        write_save(self.save_data)
        self.running = False

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
