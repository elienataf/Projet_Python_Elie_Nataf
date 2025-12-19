import sys
import pygame

from player import Player


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
        self.player = Player(name="Explorateur")

        # Petite UI de test
        self.font = pygame.font.SysFont("arial", 22)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self) -> None:
        # Ici on mettra la logique de jeu (déplacements, énigmes, etc.)
        pass

    def draw(self) -> None:
        self.screen.fill((15, 15, 25))

        title = self.font.render("Ruines Mythologiques - Prototype", True, (240, 240, 240))
        info1 = self.font.render("ECHAP : quitter", True, (200, 200, 200))
        info2 = self.font.render(f"Joueur : {self.player.name}", True, (200, 200, 200))

        self.screen.blit(title, (25, 25))
        self.screen.blit(info1, (25, 65))
        self.screen.blit(info2, (25, 95))

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
