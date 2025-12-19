import sys
import pygame
import pathlib

from player import Player
from utils import load_save, write_save
from room import Room
from enigma import enigma_sphinx, enigma_icarus, enigma_anubis
from archaeologist import Archaeologist


class Game:
    WIDTH = 900
    HEIGHT = 520
    FPS = 60

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Ruines Mythologiques - Projet B2")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        self.running = True

        # ---- Save / Player ----
        self.save_data = load_save()
        self.player = Player.from_dict(self.save_data.get("player", {}))

        # ---- Rooms progress (persistant) ----
        self.rooms_done: set[int] = set(self.save_data.get("rooms_done", []))
        self.selected_room_id: int = int(self.save_data.get("selected_room_id", 1))

        # ---- Rooms ----
        self.rooms = [
            Room(1, "Salle I — Le Sphinx", enigma_sphinx(), required_artifacts=0),
            Room(2, "Salle II — Les Ailes de Cire", enigma_icarus(), required_artifacts=0),
            Room(3, "Salle III — La Balance des Âmes (scellée)", enigma_anubis(), required_artifacts=2),
        ]

        # ---- UI ----
        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

        # ---- State machine ----
        # EXPLORE: déplacement perso + entrée dans les salles via portes
        # ENIGMA: répondre au texte
        # VICTORY: fin
        self.state = "EXPLORE"

        # ---- Enigma input ----
        self.input_text = ""
        self.max_len = 40
        self.feedback = ""

        # ---- Character (créé AVANT le scale de l'image) ----
        pos = self.save_data.get("archaeologist", {"x": 120, "y": 260})
        self.arch = Archaeologist(x=float(pos.get("x", 120)), y=float(pos.get("y", 260)))

        # ---- Sprite archéologue (APRÈS set_mode + APRÈS self.arch) ----
        assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"
        self.arch_img = pygame.image.load(assets_dir / "archeo.png").convert_alpha()
        self.arch_img = pygame.transform.scale(self.arch_img, (self.arch.w, self.arch.h))

        # ---- World layout ----
        self.world_bounds = pygame.Rect(20, 120, self.WIDTH - 40, self.HEIGHT - 160)

        # Obstacles simples (murs/piliers)
        self.obstacles = [
            pygame.Rect(250, 230, 80, 160),
            pygame.Rect(520, 200, 90, 90),
            pygame.Rect(650, 320, 140, 60),
        ]

        # Portes / zones d’entrée des salles (se mettre dedans + E)
        self.doors = {
            1: pygame.Rect(70, 150, 120, 60),
            2: pygame.Rect(70, 230, 120, 60),
            3: pygame.Rect(70, 310, 120, 60),
        }

    # -------------------- Persistence --------------------
    def save(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        self.save_data["rooms_done"] = sorted(self.rooms_done)
        self.save_data["selected_room_id"] = self.selected_room_id
        self.save_data["archaeologist"] = {"x": round(self.arch.x, 2), "y": round(self.arch.y, 2)}
        write_save(self.save_data)

    def save_and_quit(self) -> None:
        self.save()
        self.running = False

    # -------------------- Helpers --------------------
    def get_room(self, room_id: int) -> Room:
        for r in self.rooms:
            if r.room_id == room_id:
                return r
        return self.rooms[0]

    def all_rooms_done(self) -> bool:
        return all(r.room_id in self.rooms_done for r in self.rooms)

    # -------------------- UI helpers --------------------
    def draw_gradient(self) -> None:
        top = (18, 20, 32)
        bottom = (10, 10, 18)
        for y in range(self.HEIGHT):
            t = y / (self.HEIGHT - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.WIDTH, y))

    def draw_panel(self, rect: pygame.Rect, title: str | None = None) -> None:
        pygame.draw.rect(self.screen, (28, 30, 48), rect, border_radius=16)
        pygame.draw.rect(self.screen, (90, 95, 130), rect, width=2, border_radius=16)
        if title:
            t = self.font.render(title, True, (240, 240, 240))
            self.screen.blit(t, (rect.x + 16, rect.y + 12))

    def draw_input(self, rect: pygame.Rect, label: str, value: str) -> None:
        pygame.draw.rect(self.screen, (20, 22, 35), rect, border_radius=12)
        pygame.draw.rect(self.screen, (130, 130, 170), rect, width=2, border_radius=12)
        lab = self.small.render(label, True, (190, 190, 190))
        self.screen.blit(lab, (rect.x, rect.y - 22))
        txt = self.font.render(value, True, (255, 255, 255))
        self.screen.blit(txt, (rect.x + 12, rect.y + 8))

    def wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        words = text.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # -------------------- Events --------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_and_quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_and_quit()

                if self.state == "EXPLORE":
                    self.handle_explore_keys(event)
                elif self.state == "ENIGMA":
                    self.handle_enigma_keys(event)
                elif self.state == "VICTORY":
                    if event.key == pygame.K_RETURN:
                        self.state = "EXPLORE"

    def handle_explore_keys(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_e:
            arch_r = self.arch.rect()

            chosen = None
            for rid, door in self.doors.items():
                if arch_r.colliderect(door):
                    chosen = rid
                    break

            if chosen is None:
                self.feedback = "Va sur une porte puis appuie sur E."
                return

            self.selected_room_id = chosen
            room = self.get_room(chosen)

            if room.room_id in self.rooms_done:
                self.feedback = "✅ Salle déjà terminée."
                return

            if not room.is_accessible(self.player.artifacts):
                self.feedback = "🔒 Porte scellée : il faut 2 artefacts pour entrer."
                return

            self.state = "ENIGMA"
            self.input_text = ""
            self.feedback = "Tape ta réponse puis Entrée. TAB = indice."
            self.save()

    def handle_enigma_keys(self, event: pygame.event.Event) -> None:
        room = self.get_room(self.selected_room_id)

        if event.key == pygame.K_TAB:
            self.feedback = f"Indice : {room.enigma.hint}" if room.enigma.hint else "Pas d'indice."
            return

        if event.key == pygame.K_RETURN:
            self.validate_answer(room)
            return

        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return

        if event.unicode and event.unicode.isprintable():
            if len(self.input_text) < self.max_len:
                self.input_text += event.unicode

    # -------------------- Logic --------------------
    def validate_answer(self, room: Room) -> None:
        user = self.input_text.strip()
        if not user:
            self.feedback = "Tape une réponse puis appuie sur Entrée."
            return

        if room.enigma.is_correct(user):
            self.rooms_done.add(room.room_id)
            self.player.artifacts += 1

            self.feedback = "✅ Correct ! Artefact obtenu. Retour à l'exploration."
            self.input_text = ""
            self.state = "EXPLORE"

            if self.all_rooms_done():
                self.state = "VICTORY"

            self.save()
        else:
            self.feedback = "❌ Incorrect. Réessaie (TAB = indice)."
            self.input_text = ""

    def update(self) -> None:
        if self.state == "EXPLORE":
            keys = pygame.key.get_pressed()

            dx = 0.0
            dy = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_q]:
                dx -= self.arch.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += self.arch.speed
            if keys[pygame.K_UP] or keys[pygame.K_z]:
                dy -= self.arch.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += self.arch.speed

            if dx != 0 or dy != 0:
                self.arch.move(dx, dy, self.obstacles, self.world_bounds)

    # -------------------- Draw --------------------
    def draw(self) -> None:
        self.draw_gradient()

        header = pygame.Rect(20, 16, self.WIDTH - 40, 92)
        footer = pygame.Rect(20, self.HEIGHT - 36, self.WIDTH - 40, 22)
        world = self.world_bounds

        # Header
        self.draw_panel(header, None)
        title = self.font.render("🏺 Ruines Mythologiques — Exploration", True, (245, 245, 245))
        self.screen.blit(title, (header.x + 16, header.y + 14))

        sub = self.small.render(
            "Déplacement: ZQSD / Flèches  |  E: entrer  |  TAB: indice  |  ESC: quitter",
            True,
            (180, 180, 180),
        )
        self.screen.blit(sub, (header.x + 16, header.y + 48))

        stats = self.small.render(
            f"Joueur: {self.player.name}   •   Artefacts: {self.player.artifacts}   •   Salles finies: {len(self.rooms_done)}/3",
            True,
            (210, 210, 210),
        )
        self.screen.blit(stats, (header.x + 16, header.y + 70))

        # World panel
        self.draw_panel(world, "🗺️ Ruines")

        # Obstacles
        for o in self.obstacles:
            pygame.draw.rect(self.screen, (60, 55, 80), o, border_radius=10)
            pygame.draw.rect(self.screen, (110, 110, 150), o, width=2, border_radius=10)

        # Doors
        for rid, door in self.doors.items():
            room = self.get_room(rid)
            done = (rid in self.rooms_done)
            locked = (room.required_artifacts > 0 and self.player.artifacts < room.required_artifacts and not done)

            bg = (45, 85, 70) if done else (85, 70, 45)
            if locked:
                bg = (70, 45, 45)

            pygame.draw.rect(self.screen, bg, door, border_radius=12)
            pygame.draw.rect(self.screen, (200, 200, 200), door, width=2, border_radius=12)

            label = f"Salle {rid} ✅" if done else f"Salle {rid}"
            if locked:
                label += " 🔒"

            txt = self.small.render(label, True, (245, 245, 245))
            self.screen.blit(txt, (door.x + 10, door.y + 18))

        # Character sprite
        arch_r = self.arch.rect()
        self.screen.blit(self.arch_img, arch_r.topleft)

        # Enigma overlay
        if self.state == "ENIGMA":
            main = pygame.Rect(420, 140, self.WIDTH - 460, 280)
            self.draw_panel(main, "🧩 Énigme mythologique")
            room = self.get_room(self.selected_room_id)

            t = self.font.render(room.enigma.title, True, (240, 220, 160))
            self.screen.blit(t, (main.x + 16, main.y + 54))

            lines = self.wrap_text(room.enigma.question, main.w - 32, self.small)
            yy = main.y + 92
            for ln in lines[:6]:
                q = self.small.render(ln, True, (230, 230, 230))
                self.screen.blit(q, (main.x + 16, yy))
                yy += 22

            input_rect = pygame.Rect(main.x + 16, main.y + 200, main.w - 32, 44)
            self.draw_input(input_rect, "Ta réponse (texte) :", self.input_text)

            hint = self.small.render("TAB = indice  •  Entrée = valider", True, (175, 175, 175))
            self.screen.blit(hint, (main.x + 16, main.y + 255))

        # Victory overlay
        if self.state == "VICTORY":
            box = pygame.Rect(220, 180, 460, 180)
            self.draw_panel(box, "🏛️ Résultat")
            v1 = self.font.render("Victoire ! Civilisation reconstituée.", True, (200, 245, 200))
            v2 = self.small.render("Entrée : continuer à explorer | ESC : quitter", True, (190, 190, 190))
            self.screen.blit(v1, (box.x + 16, box.y + 70))
            self.screen.blit(v2, (box.x + 16, box.y + 110))

        # Footer feedback
        if self.feedback:
            fb = self.small.render(self.feedback, True, (230, 230, 230))
            self.screen.blit(fb, (footer.x + 8, footer.y))

        pygame.display.flip()

    # -------------------- Loop --------------------
    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
