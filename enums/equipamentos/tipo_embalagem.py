"""
Enumeração de tipos de embalagem.

Define os sistemas de embalagem disponíveis para equipamentos.
"""

from enum import Enum


class TipoEmbalagem(Enum):
    """
    Tipos de sistema de embalagem.

    Attributes:
        SIMPLES: Embalagem simples sem vedação especial
        VACUO: Embalagem a vácuo para conservação
        SELADORA: Sistema de selagem térmica
    """
    SIMPLES = "SIMPLES"
    VACUO = "VACUO"
    SELADORA = "SELADORA"

    def __str__(self):
        """
        Retorna a representação textual do tipo de embalagem.

        Returns:
            str: Descrição do tipo de embalagem
        """
        return self.value
