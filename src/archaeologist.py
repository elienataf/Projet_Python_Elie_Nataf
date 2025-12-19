from dataclasses import dataclass
import pygame


@dataclass
class Archaeologist:
    x: float = 120
    y: float = 260
    w: int = 28
    h: int = 36
    speed: float = 3.2

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def move(self, dx: float, dy: float, obstacles: list[pygame.Rect], bounds: pygame.Rect) -> None:
        # Move X
        self.x += dx
        r = self.rect()
        for o in obstacles:
            if r.colliderect(o):
                if dx > 0:
                    self.x = o.left - self.w
                elif dx < 0:
                    self.x = o.right
                r = self.rect()

        # Move Y
        self.y += dy
        r = self.rect()
        for o in obstacles:
            if r.colliderect(o):
                if dy > 0:
                    self.y = o.top - self.h
                elif dy < 0:
                    self.y = o.bottom
                r = self.rect()

        # Clamp to bounds
        self.x = max(bounds.left, min(self.x, bounds.right - self.w))
        self.y = max(bounds.top, min(self.y, bounds.bottom - self.h))
