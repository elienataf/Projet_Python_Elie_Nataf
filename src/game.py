import sys
import pygame

from player import Player
from utils import load_save, write_save
from room import Room
from enigma import enigma_sphinx, enigma_icarus, enigma_anubis


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
        # HUB: choisir une salle / voir progression
        # ENIGMA: répondre au texte
        # VICTORY: fin
        self.state = "HUB"

        # ---- Enigma input ----
        self.input_text = ""
        self.max_len = 40
        self.feedback = ""

    # -------------------- Persistence --------------------
    def save(self) -> None:
        self.save_data["player"] = self.player.to_dict()
        self.save_data["rooms_done"] = sorted(self.rooms_done)
        self.save_data["selected_room_id"] = self.selected_room_id
        write_save(self.save_data)

    def save_and_quit(self) -> None:
        self.save()
        self.running = False

    # -------------------- Data helpers --------------------
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

                if self.state == "HUB":
                    self.handle_hub_keys(event)
                elif self.state == "ENIGMA":
                    self.handle_enigma_keys(event)
                elif self.state == "VICTORY":
                    if event.key == pygame.K_RETURN:
                        self.state = "HUB"

    def handle_hub_keys(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_1:
            self.selected_room_id = 1
            self.feedback = ""
        if event.key == pygame.K_2:
            self.selected_room_id = 2
            self.feedback = ""
        if event.key == pygame.K_3:
            self.selected_room_id = 3
            self.feedback = ""

        if event.key == pygame.K_e:
            room = self.get_room(self.selected_room_id)

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

            self.feedback = "✅ Correct ! Artefact obtenu. Retour au camp de base."
            self.input_text = ""
            self.state = "HUB"

            if self.all_rooms_done():
                self.state = "VICTORY"

            self.save()
        else:
            self.feedback = "❌ Incorrect. Réessaie (TAB = indice)."
            self.input_text = ""

    def update(self) -> None:
        pass

    # -------------------- Draw --------------------
    def draw(self) -> None:
        self.draw_gradient()

        header = pygame.Rect(20, 16, self.WIDTH - 40, 92)
        left = pygame.Rect(20, 120, 380, self.HEIGHT - 160)
        main = pygame.Rect(420, 120, self.WIDTH - 440, self.HEIGHT - 160)
        footer = pygame.Rect(20, self.HEIGHT - 36, self.WIDTH - 40, 22)

        # Header
        self.draw_panel(header, None)
        title = self.font.render("🏺 Ruines Mythologiques — Camp de base", True, (245, 245, 245))
        self.screen.blit(title, (header.x + 16, header.y + 14))

        sub = self.small.render(
            "1/2/3 : choisir une salle  |  E : entrer  |  TAB : indice  |  ESC : quitter",
            True,
            (180, 180, 180),
        )
        self.screen.blit(sub, (header.x + 16, header.y + 48))

        stats = self.small.render(
            f"Joueur: {self.player.name}   •   Niveau: {self.player.level}   •   Artefacts: {self.player.artifacts}",
            True,
            (210, 210, 210),
        )
        self.screen.blit(stats, (header.x + 16, header.y + 70))

        # Left panel: rooms
        self.draw_panel(left, "🧭 Exploration")
        y = left.y + 52

        for r in self.rooms:
            done = "✅" if r.room_id in self.rooms_done else "⬜"
            is_selected = (r.room_id == self.selected_room_id)

            row = pygame.Rect(left.x + 14, y - 6, left.w - 28, 34)
            if is_selected:
                pygame.draw.rect(self.screen, (45, 55, 85), row, border_radius=10)
                pygame.draw.rect(self.screen, (160, 170, 220), row, width=2, border_radius=10)

            locked = (
                r.required_artifacts > 0
                and r.room_id not in self.rooms_done
                and self.player.artifacts < r.required_artifacts
            )

            lock_txt = ""
            if r.required_artifacts > 0 and r.room_id not in self.rooms_done:
                lock_txt = f"🔒 {r.required_artifacts} artefacts"

            line = f"{done}  Salle {r.room_id}"
            name = (
                r.name.replace("Salle I — ", "")
                .replace("Salle II — ", "")
                .replace("Salle III — ", "")
            )

            l1 = self.small.render(line, True, (235, 235, 235))
            l2 = self.small.render(name, True, (205, 205, 205))
            self.screen.blit(l1, (left.x + 26, y))
            self.screen.blit(l2, (left.x + 140, y))

            if lock_txt:
                c = (255, 210, 150) if locked else (180, 180, 180)
                l3 = self.small.render(lock_txt, True, c)
                self.screen.blit(l3, (left.x + 26, y + 18))

            y += 44

        tip = self.small.render(
            "Astuce: termine les salles pour reconstituer la civilisation.",
            True,
            (170, 170, 170),
        )
        self.screen.blit(tip, (left.x + 16, left.y + left.h - 32))

        # Main panel
        if self.state == "VICTORY":
            self.draw_panel(main, "🏛️ Résultat")
            v1 = self.font.render("Victoire ! Civilisation reconstituée.", True, (200, 245, 200))
            v2 = self.small.render("Entrée : revenir au camp   |   ESC : quitter", True, (190, 190, 190))
            self.screen.blit(v1, (main.x + 16, main.y + 70))
            self.screen.blit(v2, (main.x + 16, main.y + 110))

        elif self.state == "ENIGMA":
            room = self.get_room(self.selected_room_id)
            self.draw_panel(main, "🧩 Énigme mythologique")

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

        else:
            self.draw_panel(main, "📜 Briefing")
            room = self.get_room(self.selected_room_id)

            p1 = "Choisis une salle à explorer. Chaque énigme résolue te donne un artefact."
            p2 = "Certaines portes sont scellées et nécessitent un nombre d’artefacts."
            p3 = f"Salle sélectionnée : {room.name}"

            yy = main.y + 70
            for para in (p1, p2, p3):
                for ln in self.wrap_text(para, main.w - 32, self.small):
                    self.screen.blit(self.small.render(ln, True, (225, 225, 225)), (main.x + 16, yy))
                    yy += 22
                yy += 10

            cta = self.small.render(
                "Appuie sur E pour entrer dans la salle sélectionnée.",
                True,
                (190, 190, 190),
            )
            self.screen.blit(cta, (main.x + 16, main.y + main.h - 46))

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
