from dataclasses import dataclass


@dataclass
class Player:
    name: str
    level: int = 1
    artifacts: int = 0
    rooms_unlocked: int = 1

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        return cls(
            name=d.get("name", "Explorateur"),
            level=int(d.get("level", 1)),
            artifacts=int(d.get("artifacts", 0)),
            rooms_unlocked=int(d.get("rooms_unlocked", 1)),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "level": self.level,
            "artifacts": self.artifacts,
            "rooms_unlocked": self.rooms_unlocked,
        }
