from dataclasses import dataclass
from typing import Iterable


def _normalize(s: str) -> str:
    # Normalisation simple (minuscules + espaces)
    return " ".join(s.strip().lower().split())


@dataclass(frozen=True)
class Enigma:
    title: str
    question: str
    answers: tuple[str, ...]        # réponses acceptées (synonymes)
    hint: str = ""

    def is_correct(self, user_text: str) -> bool:
        u = _normalize(user_text)
        return any(u == _normalize(a) for a in self.answers)

    @classmethod
    def sample(cls) -> "Enigma":
        # 1ère énigme mythologique (simple et efficace)
        return cls(
            title="Salle I — Le Sphinx",
            question=(
                "Je marche à quatre pattes le matin, à deux le midi et à trois le soir. "
                "Qui suis-je ?"
            ),
            answers=("l'homme", "homme", "un homme", "être humain", "etre humain", "humain"),
            hint="C'est lié aux étapes de la vie (bébé, adulte, vieillesse).",
        )
