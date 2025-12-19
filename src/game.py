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
        pygame.display.set_caption("Ruines Mythologiques")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.SysFont("arial", 22)
        self.small = pygame.font.SysFont("arial", 18)

        self.assets_dir = pathlib.Path(__file__).resolve().parent.parent / "assets"
        self.save_data = load_save()

        self.world_bounds = pygame.Rect(20, 130, self.WIDTH - 40, self.HEIGHT - 170)

        self.bg_world = pygame.image.load(self.assets_dir / "bg_desert.jpeg").convert()
        self.bg_world = pygame.transform.scale(
            self.bg_world, (self.world_bounds.w, self.world_bounds.h)
        )

        self.rooms = [
            Room(1, "Salle I — Le Sphinx", enigma_sphinx(), 0),
            Room(2, "Salle II — Les Ailes de Cire", enigma_icarus(), 0),
            Room(3, "Salle III — La Balance des Âmes", enigma_anubis(), 2),
        ]

        self.state = "EXPLORE"
        self.input_text = ""
        self.max_len = 50
        self.feedback = ""
        self.show_answer = False

        self.player = Player.from_dict(self.save_data.get("player", {}))
        self.rooms_done = set(self.save_data.get("rooms_done", []))
        self.selected_room_id = 1

        self.score = int(self.save_data.get("score", 0))
        self.start_ticks = pygame.time.get_ticks()
        self.used_answer_in_room = False

        wx, wy, ww, wh = self.world_bounds

        self.arch = Archaeologist(0, 0)
        self.arch.w = 45
        self.arch.h = 52
        self.arch.speed = 3.0

        self.arch_img = pygame.image.load(self.assets_dir / "archeo.png").convert_alpha()
        self.arch_img = pygame.transform.scale(self.arch_img, (self.arch.w, self.arch.h))

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

        self.near_door_id = None

        spawn_x = wx + 40
        spawn_y = wy + wh - 90
        self.arch.x = spawn_x
        self.arch.y = spawn_y

        for _ in range(50):
            if any(self.arch.rect().colliderect(o) for o in self.obstacles):
                self.arch.x += 10
                self.arch.y -= 10
            else:
                break

        if self.FORCE_FRESH_START:
            self.rooms_done = set()
            self.score = 0
            self.start_ticks = pygame.time.get_ticks()
            self.save()

    def save(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        self.save_data["rooms_done"] = sorted(self.rooms_done)
        self.save_data["selected_room_id"] = self.selected_room_id
        self.save_data["archaeologist"] = {"x": round(self.arch.x, 2), "y": round(self.arch.y, 2)}
        self.save_data["score"] = self.score
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

    def handle_explore_keys(self, event) -> None:
        if event.key == pygame.K_e and self.near_door_id is not None:
            room = self.get_room(self.near_door_id)

            if room.room_id in self.rooms_done:
                self.feedback = "Salle déjà terminée"
                return

            if not room.is_accessible(self.player.artifacts):
                self.feedback = "Salle verrouillée"
                return

            self.selected_room_id = room.room_id
            self.state = "ENIGMA"
            self.input_text = ""
            self.used_answer_in_room = False
            self.show_answer = False
            self.feedback = ""

    def handle_enigma_keys(self, event) -> None:
        room = self.get_room(self.selected_room_id)

        if event.key == pygame.K_F2:
            self.state = "EXPLORE"
            self.input_text = ""
            self.show_answer = False
            return

        if event.key == pygame.K_F1:
            self.show_answer = True
            self.used_answer_in_room = True
            self.feedback = f"Réponse : {room.enigma.answers[0]}"
            return

        if event.key == pygame.K_TAB:
            self.feedback = room.enigma.hint
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
        if room.enigma.is_correct(self.input_text.strip()):
            self.rooms_done.add(room.room_id)
            self.player.artifacts += 1
            self.score += 100
            if self.used_answer_in_room:
                self.score -= 20
            self.state = "EXPLORE"
            if self.all_rooms_done():
                self.state = "VICTORY"
            self.save()
        else:
            self.score -= 5
            self.feedback = "Incorrect"
            self.input_text = ""

    def update(self) -> None:
        if self.state == "EXPLORE":
            keys = pygame.key.get_pressed()
            dx = dy = 0

            if keys[pygame.K_LEFT] or keys[pygame.K_q]:
                dx -= self.arch.speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += self.arch.speed
            if keys[pygame.K_UP] or keys[pygame.K_z]:
                dy -= self.arch.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += self.arch.speed

            if dx or dy:
                self.arch.move(dx, dy, self.obstacles, self.world_bounds)

            self.near_door_id = None
            for rid, door in self.doors.items():
                if self.arch.rect().colliderect(door):
                    self.near_door_id = rid
                    break

    def draw(self) -> None:
        self.screen.fill((12, 12, 18))

        header = pygame.Rect(20, 16, self.WIDTH - 40, 92)
        footer = pygame.Rect(20, self.HEIGHT - 36, self.WIDTH - 40, 22)
        world = self.world_bounds

        pygame.draw.rect(self.screen, (28, 30, 48), header, border_radius=16)
        pygame.draw.rect(self.screen, (90, 95, 130), header, 2, border_radius=16)

        title = self.font.render("Ruines Mythologiques — Map", True, (245, 245, 245))
        self.screen.blit(title, (header.x + 16, header.y + 14))

        elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
        stats = self.small.render(
            f"Score: {self.score}  Temps: {elapsed}s  Artefacts: {self.player.artifacts}  Salles: {len(self.rooms_done)}/3",
            True,
            (210, 210, 210),
        )
        self.screen.blit(stats, (header.x + 16, header.y + 60))

        self.screen.blit(self.bg_world, world.topleft)
        pygame.draw.rect(self.screen, (90, 95, 130), world, 2, border_radius=16)

        for o in self.obstacles:
            pygame.draw.rect(self.screen, (70, 65, 95), o, border_radius=12)

        for rid, door in self.doors.items():
            color = (85, 70, 45)
            if rid in self.rooms_done:
                color = (45, 85, 70)
            pygame.draw.rect(self.screen, color, door, border_radius=14)
            pygame.draw.rect(self.screen, (235, 235, 235), door, 2, border_radius=14)

            if self.near_door_id == rid:
                pygame.draw.rect(self.screen, (255, 240, 180), door, 4, border_radius=14)
                txt = self.small.render("Appuie sur E", True, (255, 240, 180))
                self.screen.blit(txt, (door.x, door.y - 22))

            label = self.small.render(f"Salle {rid}", True, (245, 245, 245))
            self.screen.blit(label, (door.x + 12, door.y + 25))

        self.screen.blit(self.arch_img, self.arch.rect().topleft)

        if self.state == "ENIGMA":
            box = pygame.Rect(430, 150, self.WIDTH - 470, 300)
            pygame.draw.rect(self.screen, (28, 30, 48), box, border_radius=16)
            pygame.draw.rect(self.screen, (90, 95, 130), box, 2, border_radius=16)

            room = self.get_room(self.selected_room_id)

            t = self.font.render(room.enigma.title, True, (240, 220, 160))
            self.screen.blit(t, (box.x + 16, box.y + 16))

            y = box.y + 50
            for line in self.wrap_text(room.enigma.question, box.w - 32, self.small):
                self.screen.blit(self.small.render(line, True, (230, 230, 230)), (box.x + 16, y))
                y += 22

            inp = pygame.Rect(box.x + 16, box.y + box.h - 60, box.w - 32, 44)
            pygame.draw.rect(self.screen, (20, 22, 35), inp, border_radius=12)
            pygame.draw.rect(self.screen, (130, 130, 170), inp, 2, border_radius=12)
            self.screen.blit(self.font.render(self.input_text, True, (255, 255, 255)), (inp.x + 12, inp.y + 8))

        if self.state == "VICTORY":
            box = pygame.Rect(220, 180, 460, 180)
            pygame.draw.rect(self.screen, (28, 30, 48), box, border_radius=16)
            pygame.draw.rect(self.screen, (90, 95, 130), box, 2, border_radius=16)
            self.screen.blit(self.font.render("Victoire !", True, (200, 245, 200)), (box.x + 16, box.y + 60))

        if self.feedback:
            self.screen.blit(self.small.render(self.feedback, True, (230, 230, 230)), (footer.x + 8, footer.y))

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()
