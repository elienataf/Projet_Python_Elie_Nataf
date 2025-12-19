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

    FORCE_FRESH_START = True

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Ruines Mythologiques - Projet B2")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

        self.assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"

        self.save_data = load_save()

        self.world_bounds = pygame.Rect(20, 130, self.WIDTH - 40, self.HEIGHT - 170)

        self.bg_world = pygame.image.load(self.assets_dir / "bg_desert.jpeg").convert()
        self.bg_world = pygame.transform.scale(self.bg_world, (self.world_bounds.w, self.world_bounds.h))

        self.rooms = [
            Room(1, "Salle I — Le Sphinx", enigma_sphinx(), required_artifacts=0),
            Room(2, "Salle II — Les Ailes de Cire", enigma_icarus(), required_artifacts=0),
            Room(3, "Salle III — La Balance des Âmes (scellée)", enigma_anubis(), required_artifacts=2),
        ]

        self.state = "EXPLORE"  

        self.input_text = ""
        self.max_len = 50
        self.feedback = ""
        self.show_answer = False

        self.player = Player.from_dict(self.save_data.get("player", {}))
        self.rooms_done: set[int] = set(self.save_data.get("rooms_done", []))
        self.selected_room_id: int = int(self.save_data.get("selected_room_id", 1))

        pos = self.save_data.get("archaeologist", {"x": 0, "y": 0})
        self.arch = Archaeologist(x=float(pos.get("x", 0)), y=float(pos.get("y", 0)))
        self.arch.w = 38
        self.arch.h = 54
        self.arch.speed = 3.0

        self.arch_img = pygame.image.load(self.assets_dir / "archeo.png").convert_alpha()
        self.arch_img = pygame.transform.scale(self.arch_img, (self.arch.w, self.arch.h))

        wx, wy, ww, wh = self.world_bounds

        self.obstacles = [
            pygame.Rect(wx + 250, wy + 85, 95, 220),
            pygame.Rect(wx + 560, wy + 55, 110, 110),
            pygame.Rect(wx + 640, wy + 235, 170, 70),
            pygame.Rect(wx + 140, wy + 300, 370, 25),
            pygame.Rect(wx + 440, wy + 210, 75, 75),
            pygame.Rect(wx + 90, wy + 170, 85, 85),
        ]

        self.doors = {
            1: pygame.Rect(wx + 70, wy + 55, 160, 70),
            2: pygame.Rect(wx + 370, wy + 35, 170, 70),
            3: pygame.Rect(wx + 120, wy + 230, 170, 70),
        }

        default_spawn_x = wx + 40
        default_spawn_y = wy + wh - 90


        if self.FORCE_FRESH_START:
            self.rooms_done = set()
            self.selected_room_id = 1
            self.player.artifacts = 0
            self.player.level = 1
            self.player.rooms_unlocked = 1

            self.arch.x = default_spawn_x
            self.arch.y = default_spawn_y

            self.save()
        else:
            self.arch.x = max(wx, min(self.arch.x, wx + ww - self.arch.w))
            self.arch.y = max(wy, min(self.arch.y, wy + wh - self.arch.h))

    def save(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        self.save_data["rooms_done"] = sorted(self.rooms_done)
        self.save_data["selected_room_id"] = self.selected_room_id
        self.save_data["archaeologist"] = {"x": round(self.arch.x, 2), "y": round(self.arch.y, 2)}
        write_save(self.save_data)

    def save_and_quit(self) -> None:
        self.save()
        self.running = False

    def get_room(self, room_id: int) -> Room:
        for r in self.rooms:
            if r.room_id == room_id:
                return r
        return self.rooms[0]

    def all_rooms_done(self) -> bool:
        return all(r.room_id in self.rooms_done for r in self.rooms)

    def room_correct_answer(self, room: Room) -> str:
        return room.enigma.answers[0] if room.enigma.answers else "(pas de réponse)"

    def draw_panel(self, rect: pygame.Rect, title: str | None = None, fill: bool = True) -> None:
        if fill:
            pygame.draw.rect(self.screen, (28, 30, 48), rect, border_radius=16)
        pygame.draw.rect(self.screen, (90, 95, 130), rect, width=2, border_radius=16)
        if title:
            lab = self.font.render(title, True, (220, 220, 220))
            self.screen.blit(lab, (rect.x + 16, rect.y + 16))


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
                self.feedback = "Va sur une salle (zone) puis appuie sur E."
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
            self.show_answer = False
            self.feedback = "Entrée: valider | TAB: indice | F1: réponse | F2: quitter la salle"
            self.save()

    def handle_enigma_keys(self, event: pygame.event.Event) -> None:
        room = self.get_room(self.selected_room_id)

        if event.key == pygame.K_F2:
            self.state = "EXPLORE"
            self.input_text = ""
            self.show_answer = False
            self.feedback = "Retour sur la map."
            self.save()
            return

        if event.key == pygame.K_F1:
            self.show_answer = True
            self.feedback = f"💡 Réponse : {self.room_correct_answer(room)} (tu peux encore répondre)"
            return

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

    def validate_answer(self, room: Room) -> None:
        user = self.input_text.strip()
        if not user:
            self.feedback = "Tape une réponse puis Entrée."
            return

        if room.enigma.is_correct(user):
            self.rooms_done.add(room.room_id)
            self.player.artifacts += 1

            self.feedback = "✅ Correct ! Artefact obtenu. Retour à la map."
            self.input_text = ""
            self.show_answer = False
            self.state = "EXPLORE"

            if self.all_rooms_done():
                self.state = "VICTORY"

            self.save()
        else:
            self.feedback = "❌ Incorrect. TAB=indice | F1=réponse | F2=quitter"
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

    def draw(self) -> None:
        self.screen.fill((12, 12, 18))

        header = pygame.Rect(20, 16, self.WIDTH - 40, 92)
        footer = pygame.Rect(20, self.HEIGHT - 36, self.WIDTH - 40, 22)
        world = self.world_bounds

        self.draw_panel(header, None)
        title = self.font.render("🏺 Ruines Mythologiques — Map", True, (245, 245, 245))
        self.screen.blit(title, (header.x + 16, header.y + 14))

        sub = self.small.render(
            "Déplacement: ZQSD / Flèches  |  E: entrer  |  ESC: quitter",
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

        self.screen.blit(self.bg_world, world.topleft)
        self.draw_panel(world, "🗺️ Ruines", fill=False)


        for o in self.obstacles:
            pygame.draw.rect(self.screen, (60, 55, 80), o, border_radius=12)
            pygame.draw.rect(self.screen, (130, 130, 170), o, width=2, border_radius=12)

        for rid, door in self.doors.items():
            room = self.get_room(rid)
            done = (rid in self.rooms_done)
            locked = (room.required_artifacts > 0 and self.player.artifacts < room.required_artifacts and not done)

            bg = (45, 85, 70) if done else (85, 70, 45)
            if locked:
                bg = (70, 45, 45)

            pygame.draw.rect(self.screen, bg, door, border_radius=14)
            pygame.draw.rect(self.screen, (235, 235, 235), door, width=2, border_radius=14)

            label = f"Salle {rid} ✅" if done else f"Salle {rid}"
            if locked:
                label += " 🔒"
            txt = self.small.render(label, True, (245, 245, 245))
            self.screen.blit(txt, (door.x + 12, door.y + 25))

        arch_r = self.arch.rect()
        self.screen.blit(self.arch_img, arch_r.topleft)

        if self.state == "ENIGMA":
            main = pygame.Rect(430, 150, self.WIDTH - 470, 300)
            self.draw_panel(main, "🧩 Énigme")

            room = self.get_room(self.selected_room_id)

            t = self.font.render(room.enigma.title, True, (240, 220, 160))
            self.screen.blit(t, (main.x + 16, main.y + 54))

            lines = self.wrap_text(room.enigma.question, main.w - 32, self.small)
            yy = main.y + 92
            for ln in lines[:6]:
                q = self.small.render(ln, True, (230, 230, 230))
                self.screen.blit(q, (main.x + 16, yy))
                yy += 22

            input_rect = pygame.Rect(main.x + 16, main.y + 210, main.w - 32, 44)
            self.draw_input(input_rect, "Réponse (texte) :", self.input_text)

            hint = self.small.render("TAB: indice | F1: réponse | F2: quitter | Entrée: valider", True, (175, 175, 175))
            self.screen.blit(hint, (main.x + 16, main.y + 265))

            if self.show_answer:
                ans = self.small.render(f"Réponse: {self.room_correct_answer(room)}", True, (255, 220, 160))
                self.screen.blit(ans, (main.x + 16, main.y + 285))

        if self.state == "VICTORY":
            box = pygame.Rect(220, 180, 460, 180)
            self.draw_panel(box, "🏛️ Résultat")
            v1 = self.font.render("Victoire ! Civilisation reconstituée.", True, (200, 245, 200))
            v2 = self.small.render("Entrée : continuer | ESC : quitter", True, (190, 190, 190))
            self.screen.blit(v1, (box.x + 16, box.y + 70))
            self.screen.blit(v2, (box.x + 16, box.y + 110))

        if self.feedback:
            fb = self.small.render(self.feedback, True, (230, 230, 230))
            self.screen.blit(fb, (footer.x + 8, footer.y))

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
