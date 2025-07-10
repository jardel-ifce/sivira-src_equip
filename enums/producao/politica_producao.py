from enum import Enum

class PoliticaProducao(Enum):
    """
    Enumeração para representar os modos de produção.
    """
    SOB_DEMANDA = "SOB_DEMANDA"
    ESTOCADO = "ESTOCADO"
    AMBOS = "AMBOS"

    def __str__(self):
        """
        Retorna a representação textual do modo de produção.
        """
        return self.name