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
            "Dans le désert égyptien, je pointe vers le ciel, "
            "gardienne de pharaons et de mystères éternels. "
            "Qu'est-ce que je suis ?"
        ),
        answers=("une pyramide", "pyramide"),
        hint="Je suis une structure emblématique d'Égypte.",
    )


def enigma_icarus() -> Enigma:
    return Enigma(
        title="Salle II — Les Ailes de Cire",
        question=(
            "Cité perdue des Incas, perchée dans les Andes, révélée au monde en 1911. "
            "Quel est son nom ?"
        ),
        answers=("machu picchu",),
        hint="Je suis une ancienne cité inca célèbre.",
    )


def enigma_anubis() -> Enigma:
    return Enigma(
        title="Salle III — La Balance des Âmes",
        question=(
            "Écriture antique, gravée sur pierre, qui raconte guerres et rois sans un son. "
            "Qu'est-ce que je suis ?"
        ),
        answers=("hiéroglyphes", "hiéroglyphe"),
        hint="Je suis un système d'écriture ancien.",
    )
