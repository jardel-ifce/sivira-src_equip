from enum import Enum

class TipoVelocidade(Enum):
    BAIXA = "Baixa"
    MEDIA = "Media"
    ALTA = "Alta"

    def __str__(self):
        return self.value
