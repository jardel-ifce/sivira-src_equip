from enum import Enum
class TipoMistura(Enum):
    """
    Enumeração que representa os ritmos de execução dos equipamentos.
    """
    LENTA = "Lenta"
    RAPIDA = "Rápida"
    SEMI_RAPIDA = "Semi-rápida"

    def __str__(self):
        return self.value