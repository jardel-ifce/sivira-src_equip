"""
Enumeração de velocidades de operação.

Define os níveis de velocidade para equipamentos rotativos.
"""

from enum import Enum


class TipoVelocidade(Enum):
    """
    Velocidades de operação de equipamentos.

    Attributes:
        BAIXA: Velocidade baixa de rotação
        MEDIA: Velocidade média de rotação
        ALTA: Velocidade alta de rotação
    """
    BAIXA = "Baixa"
    MEDIA = "Media"
    ALTA = "Alta"

    def __str__(self):
        """
        Retorna a representação textual da velocidade.

        Returns:
            str: Descrição da velocidade
        """
        return self.value