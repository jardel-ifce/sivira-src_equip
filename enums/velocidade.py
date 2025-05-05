from enum import Enum

class Velocidade(Enum):
    BAIXA = "Baixa"
    MEDIA = "Media"
    ALTA = "Alta"

    def __str__(self):
        return self.value
