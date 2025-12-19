from dataclasses import dataclass


@dataclass
class Player:
    name: str
    level: int = 1
    artifacts: int = 0
    rooms_unlocked: int = 1
