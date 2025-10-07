"""
Enumeração de velocidades de mistura.

Define os ritmos de execução dos equipamentos de mistura.
"""

from enum import Enum


class TipoMistura(Enum):
    """
    Velocidades de mistura de equipamentos.

    Attributes:
        LENTA: Mistura em velocidade lenta
        RAPIDA: Mistura em velocidade rápida
        SEMI_RAPIDA: Mistura em velocidade intermediária
    """
    LENTA = "Lenta"
    RAPIDA = "Rápida"
    SEMI_RAPIDA = "Semi-rápida"

    def __str__(self):
        """
        Retorna a representação textual da velocidade de mistura.

        Returns:
            str: Descrição da velocidade de mistura
        """
        return self.value
