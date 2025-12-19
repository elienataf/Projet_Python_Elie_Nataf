from dataclasses import dataclass
from enigma import Enigma


@dataclass(frozen=True)
class Room:
    room_id: int
    name: str
    enigma: Enigma
    required_artifacts: int = 0  # pour entrer dans la salle

    def is_accessible(self, artifacts: int) -> bool:
        return artifacts >= self.required_artifacts
