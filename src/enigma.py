from dataclasses import dataclass


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


@dataclass(frozen=True)
class Enigma:
    title: str
    question: str
    answers: tuple[str, ...]
    hint: str = ""

    def is_correct(self, user_text: str) -> bool:
        u = _normalize(user_text)
        return any(u == _normalize(a) for a in self.answers)


def enigma_sphinx() -> Enigma:
    return Enigma(
        title="Salle I — Le Sphinx",
        question=(
            "Je marche à quatre pattes le matin, à deux le midi et à trois le soir. "
            "Qui suis-je ?"
        ),
        answers=("l'homme", "homme", "un homme", "être humain", "etre humain", "humain"),
        hint="C'est lié aux étapes de la vie (bébé, adulte, vieillesse).",
    )


def enigma_icarus() -> Enigma:
    return Enigma(
        title="Salle II — Les Ailes de Cire",
        question="Quel héros grec est tombé dans la mer après s'être approché trop près du soleil ?",
        answers=("icare", "icarus", "icar"),
        hint="Son père est Dédale.",
    )


def enigma_anubis() -> Enigma:
    return Enigma(
        title="Salle III — La Balance des Âmes",
        question="Dans la mythologie égyptienne, quel dieu à tête de chacal est lié à l'embaumement ?",
        answers=("anubis",),
        hint="On le voit souvent près des momies.",
    )
